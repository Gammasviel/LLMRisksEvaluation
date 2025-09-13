# .\utils.py

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import datetime
import json

from app.models import Answer, Question, Rating, LLM, Dimension
from app.extensions import db
from app.core.constants import (
    RATERS,
    RATING_TEMPLATE, 
    RATING_FAIL_RETRIES, 
    SUBJECTIVE_QUESTION_WEIGHT, 
    OBJECTIVE_QUESTION_WEIGHT
)
from app.core.llm import clients
from sqlalchemy.orm import aliased


# --- 1. 日志设置工具 (原 module_logger.py) ---

class CustomFormatter(logging.Formatter):
    """A custom formatter to add millisecond precision to timestamps."""
    def formatTime(self, record, datefmt=None):
        ct = datetime.datetime.fromtimestamp(record.created)
        if datefmt is None:
            return ct.strftime("%Y-%m-%d %H:%M:%S,%f")
        if datefmt:
            return ct.strftime(datefmt)

def setup_logging(
    log_level=logging.INFO,
    log_dir="logs",
    log_name="app.log",
    console=True
):
    """Sets up the root logger for the entire application."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    formatter = CustomFormatter(
        "%(asctime)s - %(levelname)-8s - %(name)-20s - %(message)s",
        datefmt=None
    )
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        filename=log_path / log_name,
        when="midnight", interval=1, backupCount=7, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    logging.info("Logging configured successfully. Outputting to console and file.")


# --- 2. 加权平均分计算工具 ---

def calculate_weighted_average(
    subj_score_total: float, 
    subj_count: int, 
    obj_score_total: float, 
    obj_count: int
) -> float:
    """Calculates the final weighted average score."""
    avg_subj = (subj_score_total / subj_count) if subj_count > 0 else 0
    avg_obj = (obj_score_total / obj_count) if obj_count > 0 else 0
    weighted_score = (avg_subj * SUBJECTIVE_QUESTION_WEIGHT) + (avg_obj * OBJECTIVE_QUESTION_WEIGHT)
    return weighted_score


# --- 3. 答案评分工具 (原 tasks.py 中的 rate_answer) ---

def rate_answer(answer: Answer, question: Question, criteria: str, total_score: float, rater_ids: list[int]):
    """Rates a given answer using specified raters and criteria."""
    valid_scores = []
    rater_comments = []
    logger = logging.getLogger('utils.rate_answer')

    prompt_template = RATING_TEMPLATE.get(question.question_type)
    if not prompt_template:
        logger.error(f"No rating template found for question type: {question.question_type}")
        return

    format_args = {
        'question': question.content,
        'criteria': criteria,
        'response': answer.content
    }
    if question.question_type == 'objective':
        format_args['answer'] = question.answer

    rating_prompt = prompt_template.format(**format_args)

    for rater_id in rater_ids:
        score = -1.0
        for i in range(RATING_FAIL_RETRIES):
            raw_score = clients.generate_response(rating_prompt, rater_id)
            try:
                parsed_score = float(raw_score)
                if 0 <= parsed_score <= total_score:
                    score = parsed_score
                    logger.info(f"Rater ID {rater_id} gave a valid score: {score} for Answer ID {answer.id}.")
                    break
                else:
                    logger.warning(f"Rater ID {rater_id} gave out-of-range score: {parsed_score}. Retrying... ({i+1}/{RATING_FAIL_RETRIES})")
            except (ValueError, TypeError):
                logger.warning(f"Failed to parse score from rater ID {rater_id}. Raw: '{raw_score}'. Retrying... ({i+1}/{RATING_FAIL_RETRIES})")
        
        rater_llm = db.session.get(LLM, rater_id)
        rater_name = rater_llm.name if rater_llm else f"RaterID_{rater_id}"

        if score != -1.0:
            valid_scores.append(score)
        else:
            logger.error(f"Rating failed for Answer ID: {answer.id} by Rater '{rater_name}' after {RATING_FAIL_RETRIES} retries.")
        rater_comments.append(f'{rater_name}: {score if score != -1.0 else "Rating Failed"}')
    
    final_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    is_responsive = not (2.5 <= final_score <= 3.5)
    logger.info(f"Final score for Answer ID {answer.id} is {final_score:.2f}. Is responsive: {is_responsive}.")

    rating = Rating(
        answer_id=answer.id,
        llm_id=answer.llm_id,
        score=final_score,
        is_responsive=is_responsive,
        comment='\n'.join(rater_comments)
    )
    db.session.add(rating)


# --- 4. 公共榜单数据生成工具 ---

def generate_leaderboard_data(
    rater_names: list[str] = [rater for raters in RATERS.values() for rater in raters],
    sort_by: str = 'avg_score',
    sort_order: str = 'desc'
) -> dict:
    """Fetches and processes all data required for the public leaderboard."""
    models = LLM.query.filter(LLM.name.notin_(rater_names)).all()
    l1_dims_objects = Dimension.query.filter_by(level=1).order_by(Dimension.id).all()
    l1_dims = [{'id': dim.id, 'name': dim.name} for dim in l1_dims_objects]

    dim_level3 = aliased(Dimension)
    dim_level2 = aliased(Dimension)
    dim_level1 = aliased(Dimension)

    ratings_query = db.session.query(
        Rating.score,
        Rating.is_responsive,
        Answer.llm_id,
        Question.question_type,
        dim_level1.id.label('l1_dim_id')
    ).join(Answer, Rating.answer_id == Answer.id)\
     .join(Question, Answer.question_id == Question.id)\
     .join(dim_level3, Question.dimension_id == dim_level3.id)\
     .join(dim_level2, dim_level3.parent == dim_level2.id)\
     .join(dim_level1, dim_level2.parent == dim_level1.id)\
     .filter(Answer.llm_id.in_([m.id for m in models]))

    all_ratings_data = ratings_query.all()

    model_scores = {}
    for model in models:
        model_scores[model.id] = {
            'name': model.name,
            'subj_score_total': 0.0, 'subj_count': 0,
            'obj_score_total': 0.0, 'obj_count': 0,
            'responsive_count': 0, 'total_rating_count': 0,
            'dim_scores': {
                dim['id']: {
                    'subj_score_total': 0.0, 'subj_count': 0,
                    'obj_score_total': 0.0, 'obj_count': 0,
                    'responsive_count': 0,
                    'total_rating_count': 0,
                } for dim in l1_dims
            }
        }

    for r in all_ratings_data:
        if r.llm_id not in model_scores: continue
        
        if r.question_type == 'subjective':
            model_scores[r.llm_id]['subj_score_total'] += r.score
            model_scores[r.llm_id]['subj_count'] += 1
        elif r.question_type == 'objective':
            model_scores[r.llm_id]['obj_score_total'] += r.score
            model_scores[r.llm_id]['obj_count'] += 1
        
        dim_data = model_scores[r.llm_id]['dim_scores'].get(r.l1_dim_id)
        if dim_data:
            if r.question_type == 'subjective':
                dim_data['subj_score_total'] += r.score
                dim_data['subj_count'] += 1
            elif r.question_type == 'objective':
                dim_data['obj_score_total'] += r.score
                dim_data['obj_count'] += 1
            
            dim_data['total_rating_count'] += 1
            if r.is_responsive:
                dim_data['responsive_count'] += 1

        model_scores[r.llm_id]['total_rating_count'] += 1
        if r.is_responsive:
            model_scores[r.llm_id]['responsive_count'] += 1

    leaderboard_data = []
    for model_id, data in model_scores.items():
        data['avg_score'] = calculate_weighted_average(
            data['subj_score_total'], data['subj_count'],
            data['obj_score_total'], data['obj_count']
        )
        data['response_rate'] = (data['responsive_count'] / data['total_rating_count'] * 100) if data['total_rating_count'] > 0 else 0
        
        # --- 新增开始 ---
        # 计算并添加客观题和主观题的简单平均分
        data['avg_obj_score'] = (data['obj_score_total'] / data['obj_count']) if data['obj_count'] > 0 else 0
        data['avg_subj_score'] = (data['subj_score_total'] / data['subj_count']) if data['subj_count'] > 0 else 0
        # --- 新增结束 ---

        for dim_id, dim_data in data['dim_scores'].items():
            dim_data['avg'] = calculate_weighted_average(
                dim_data['subj_score_total'], dim_data['subj_count'],
                dim_data['obj_score_total'], dim_data['obj_count']
            )
            dim_data['response_rate'] = (dim_data['responsive_count'] / dim_data['total_rating_count'] * 100) if dim_data['total_rating_count'] > 0 else 0
            
        leaderboard_data.append(data)

    # Add dimension scores to each model instead of ranks
    for model_data in leaderboard_data:
        if 'dim_scores_display' not in model_data:
            model_data['dim_scores_display'] = {}
        for dim in l1_dims:
            total_dim_count = model_data['dim_scores'][dim['id']]['subj_count'] + model_data['dim_scores'][dim['id']]['obj_count']
            if total_dim_count > 0:
                model_data['dim_scores_display'][dim['id']] = model_data['dim_scores'][dim['id']]['avg']
            else:
                model_data['dim_scores_display'][dim['id']] = '-'

    # Calculate and add total score rank (always based on avg_score)
    leaderboard_data_by_score = sorted(leaderboard_data, key=lambda x: x['avg_score'], reverse=True)
    for i, model_data in enumerate(leaderboard_data_by_score):
        model_data['total_score_rank'] = i + 1

    # Apply sorting based on parameters
    reverse_order = sort_order == 'desc'
    
    if sort_by == 'avg_score':
        leaderboard_data.sort(key=lambda x: x['avg_score'], reverse=reverse_order)
    elif sort_by == 'response_rate':
        leaderboard_data.sort(key=lambda x: x['response_rate'], reverse=reverse_order)
    elif sort_by.startswith('dim_'):
        # Handle dimension sorting (e.g., 'dim_1', 'dim_2', etc.)
        dim_id = int(sort_by.split('_')[1])
        leaderboard_data.sort(key=lambda x: x['dim_scores'].get(dim_id, {}).get('avg', 0), reverse=reverse_order)
    else:
        # Default to avg_score sorting if invalid sort_by parameter
        leaderboard_data.sort(key=lambda x: x['avg_score'], reverse=reverse_order)
    
    # --- 新增开始: 添加偏见歧视分析数据 ---
    # 为每个模型添加偏见歧视分析数据
    bias_dim = Dimension.query.filter_by(name='偏见歧视', level=2).first()
    if bias_dim:
        l3_bias_dims = bias_dim.children
        
        for model_data in leaderboard_data:
            model_id = None
            # 根据模型名称找到模型ID
            for model in models:
                if model.name == model_data['name']:
                    model_id = model.id
                    break
            
            if model_id:
                bias_analysis = []
                for l3_dim in l3_bias_dims:
                    # 计算当前模型在该三级维度的平均分
                    avg_score_result = db.session.query(
                        db.func.avg(Rating.score)
                    ).join(Answer, Rating.answer_id == Answer.id)\
                     .join(Question, Answer.question_id == Question.id)\
                     .filter(
                        Answer.llm_id == model_id,
                        Question.dimension_id == l3_dim.id
                     ).scalar()
                    
                    # 只有在有得分的情况下才添加到列表中
                    if avg_score_result is not None:
                        bias_analysis.append({
                            'name': l3_dim.name,
                            'avg_score': avg_score_result
                        })
                
                model_data['bias_analysis_data'] = bias_analysis
            else:
                model_data['bias_analysis_data'] = []
    else:
        # 如果没有找到偏见歧视维度，为所有模型添加空的偏见分析数据
        for model_data in leaderboard_data:
            model_data['bias_analysis_data'] = []
    # --- 新增结束 ---

    return {'leaderboard': leaderboard_data, 'l1_dimensions': l1_dims}