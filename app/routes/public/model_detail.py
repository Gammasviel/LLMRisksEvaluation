
import logging
from flask import Blueprint, render_template, flash, redirect, url_for
from app.models import Question, LLM, Dimension, Answer, Rating
from app.extensions import db, icons
from app.core.utils import generate_leaderboard_data

model_detail_bp = Blueprint('model_detail', __name__, url_prefix='/model/detail/')
logger = logging.getLogger('model_detail_routes')

@model_detail_bp.route('/<model_name>')
def model_detail(model_name):
    logger.info(f"Accessing detail page for model: {model_name}")
    
    llm = LLM.query.filter_by(name=model_name).first_or_404()
    
    # 1. Get full leaderboard data to find the rank and model details
    full_leaderboard_data = generate_leaderboard_data()
    
    model_data = None
    model_rank = -1
    for i, data in enumerate(full_leaderboard_data['leaderboard']):
        if data['name'] == model_name:
            model_data = data
            model_rank = i + 1
            break
            
    if not model_data:
        flash('未找到该模型的评估数据。', 'warning')
        return redirect(url_for('public_leaderboard.display_public_leaderboard'))

    # 2. Prepare data for Chart 1: Radar Chart ((n+1) dimensions)
    radar_indicators = []
    radar_values = []
    
    # Add response rate first
    radar_indicators.append({'name': '响应率', 'max': 100})
    radar_values.append(model_data['response_rate'])
    
    # Add L1 dimension scores
    for dim in full_leaderboard_data['l1_dimensions']:
        radar_indicators.append({'name': dim['name'], 'max': 5}) # Assuming max score is 5
        score = model_data['dim_scores'][dim['id']]['avg']
        radar_values.append(score)

    radar_data = {
        'indicators': radar_indicators,
        'values': radar_values
    }

    # 3. Prepare data for Chart 2: Proportional Bar Chart
    # We will use a horizontal stacked bar chart to show proportions
    bar_data = []
    total_score_sum = 0
    for dim in full_leaderboard_data['l1_dimensions']:
        score = model_data['dim_scores'][dim['id']]['avg']
        # Only include dimensions where the model was actually evaluated
        if model_data['dim_scores'][dim['id']]['subj_count'] + model_data['dim_scores'][dim['id']]['obj_count'] > 0:
            bar_data.append({'name': dim['name'], 'value': score})
            total_score_sum += score
    
    # Calculate percentage for each dimension's score relative to the sum of scores
    if total_score_sum > 0:
        for item in bar_data:
            item['percentage'] = (item['value'] / total_score_sum) * 100

    # 4. Prepare data for dimension-wise response rates
    response_rate_data = []
    for dim in full_leaderboard_data['l1_dimensions']:
        dim_data = model_data['dim_scores'][dim['id']]
        total_count = dim_data['subj_count'] + dim_data['obj_count']
        
        # --- 修改开始 ---
        # 原来的代码使用了总体的响应率作为近似值
        # response_rate = model_data['response_rate'] if total_count > 0 else 0
        
        # 使用新计算的、精确的各维度响应率
        response_rate = dim_data.get('response_rate', 0) if total_count > 0 else 0
        # --- 修改结束 ---
        
        response_rate_data.append({'name': dim['name'], 'value': response_rate})
    
    # --- 新增开始: 模型偏见歧视分析 ---
    bias_analysis_data = []
    # 1. 查找名为“偏见歧视”的二级维度
    bias_dim = Dimension.query.filter_by(name='偏见歧视', level=2).first()
    
    if bias_dim:
        # 2. 获取其下的所有三级维度
        l3_bias_dims = bias_dim.children
        
        for l3_dim in l3_bias_dims:
            # 3. 对每个三级维度，计算当前模型的平均分
            avg_score_result = db.session.query(
                db.func.avg(Rating.score)
            ).join(Answer, Rating.answer_id == Answer.id)\
             .join(Question, Answer.question_id == Question.id)\
             .filter(
                Answer.llm_id == llm.id,
                Question.dimension_id == l3_dim.id
             ).scalar()
            
            # 只有在有得分的情况下才添加到列表中
            if avg_score_result is not None:
                bias_analysis_data.append({
                    'name': l3_dim.name,
                    'avg_score': avg_score_result
                })
    else:
        logger.warning("Level 2 Dimension '偏见歧视' not found in the database. Bias analysis will be skipped.")
    # --- 新增结束 ---

    return render_template(
        'public/model_detail.html', 
        llm=llm,
        model_rank=model_rank,
        radar_data=radar_data,
        bar_data=bar_data,
        response_rate_data=response_rate_data,
        icons=icons,
        bias_analysis_data=bias_analysis_data  # 将新数据传递给模板
    )