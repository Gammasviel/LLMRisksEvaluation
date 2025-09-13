# .\routes\dev_history.py

from flask import Blueprint, render_template, request, flash, redirect, url_for
import logging
from app.models import EvaluationHistory, Question
from app.extensions import db
from app.core.constants import QUADRANT_SCORE_THRESHOLD, QUADRANT_RESPONSE_RATE_THRESHOLD
from app.core.utils import generate_leaderboard_data
from app.routes.dev.auth import admin_required
from flask_login import login_required

dev_history_bp = Blueprint('dev_history', __name__, url_prefix='/dev/history')
logger = logging.getLogger('dev_history_routes')

@dev_history_bp.route('/')
@login_required
@admin_required
def dev_history():
    """开发版历史记录页面"""
    logger.info("Accessing dev history page.")
    
    try:
        # 获取所有历史记录，按时间倒序
        history_records = EvaluationHistory.query.order_by(EvaluationHistory.timestamp.desc()).all()
        
        return render_template('dev/dev_history.html', history_records=history_records)
    except Exception as e:
        logger.error(f"Error loading dev history: {e}", exc_info=True)
        flash('加载历史记录时发生错误，请检查日志。', 'danger')
        return render_template('dev/dev_history.html', history_records=[])

@dev_history_bp.route('/delete/<int:history_id>', methods=['POST'])
def delete_history_record(history_id):
    """删除历史记录"""
    logger.info(f"Received request to delete history record {history_id}.")
    
    try:
        history_record = EvaluationHistory.query.get_or_404(history_id)
        timestamp = history_record.timestamp.strftime('%Y年%m月%d日 %H:%M:%S')
        
        db.session.delete(history_record)
        db.session.commit()
        
        flash(f'成功删除历史记录：{timestamp}', 'success')
        logger.info(f"Successfully deleted history record {history_id}")
        
    except Exception as e:
        logger.error(f"Failed to delete history record {history_id}: {e}", exc_info=True)
        flash('删除历史记录时发生错误，请检查日志。', 'danger')
        db.session.rollback()
    
    return redirect(url_for('dev_history.dev_history'))

@dev_history_bp.route('/save', methods=['POST'])
def save_current_data_to_history():
    """保存当前评估数据到历史记录"""
    logger.info("Received request to save current evaluation data to history.")
    
    try:
        # 获取当前评估数据
        current_data = generate_leaderboard_data()
        
        # 获取题目总数
        total_questions = Question.query.count()
        
        # 创建历史记录
        history_record = EvaluationHistory(
            dimensions=current_data['l1_dimensions'],
            evaluation_data=current_data['leaderboard'],
            extra_info={
                'score_threshold': QUADRANT_SCORE_THRESHOLD,
                'rate_threshold': QUADRANT_RESPONSE_RATE_THRESHOLD,
                'total_models': len(current_data['leaderboard']),
                'total_dimensions': len(current_data['l1_dimensions']),
                'total_questions': total_questions,
                'manual_save': True  # 标记为手动保存
            }
        )
        
        db.session.add(history_record)
        db.session.commit()
        
        flash(f'成功保存当前评估数据到历史记录！包含 {len(current_data["leaderboard"])} 个模型的数据。', 'success')
        logger.info(f"Successfully saved current evaluation data to history with {len(current_data['leaderboard'])} models")
        
    except Exception as e:
        logger.error(f"Failed to save current data to history: {e}", exc_info=True)
        flash('保存历史记录时发生错误，请检查日志。', 'danger')
        db.session.rollback()
    
    return redirect(url_for('index.index'))