
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

    radar_indicators = []
    radar_values = []
    
    radar_indicators.append({'name': '响应率', 'max': 100})
    radar_values.append(model_data['response_rate'])
    
    for dim in full_leaderboard_data['l1_dimensions']:
        radar_indicators.append({'name': dim['name'], 'max': 5})
        score = model_data['dim_scores'][dim['id']]['avg']
        radar_values.append(score)

    radar_data = {
        'indicators': radar_indicators,
        'values': radar_values
    }

    bar_data = []
    total_score_sum = 0
    for dim in full_leaderboard_data['l1_dimensions']:
        score = model_data['dim_scores'][dim['id']]['avg']
        if model_data['dim_scores'][dim['id']]['subj_count'] + model_data['dim_scores'][dim['id']]['obj_count'] > 0:
            bar_data.append({'name': dim['name'], 'value': score})
            total_score_sum += score
    
    if total_score_sum > 0:
        for item in bar_data:
            item['percentage'] = (item['value'] / total_score_sum) * 100

    response_rate_data = []
    for dim in full_leaderboard_data['l1_dimensions']:
        dim_data = model_data['dim_scores'][dim['id']]
        total_count = dim_data['subj_count'] + dim_data['obj_count']
        
        response_rate = dim_data.get('response_rate', 0) if total_count > 0 else 0
        
        response_rate_data.append({'name': dim['name'], 'value': response_rate})
    
    bias_analysis_data = []
    bias_dim = Dimension.query.filter_by(name='偏见歧视', level=2).first()
    
    if bias_dim:
        l3_bias_dims = bias_dim.children
        
        for l3_dim in l3_bias_dims:
            avg_score_result = db.session.query(
                db.func.avg(Rating.score)
            ).join(Answer, Rating.answer_id == Answer.id)\
             .join(Question, Answer.question_id == Question.id)\
             .filter(
                Answer.llm_id == llm.id,
                Question.dimension_id == l3_dim.id
             ).scalar()
            
            if avg_score_result is not None:
                bias_analysis_data.append({
                    'name': l3_dim.name,
                    'avg_score': avg_score_result
                })
    else:
        logger.warning("Level 2 Dimension '偏见歧视' not found in the database. Bias analysis will be skipped.")

    return render_template(
        'public/model_detail.html', 
        llm=llm,
        model_rank=model_rank,
        radar_data=radar_data,
        bar_data=bar_data,
        response_rate_data=response_rate_data,
        icons=icons,
        bias_analysis_data=bias_analysis_data
    )