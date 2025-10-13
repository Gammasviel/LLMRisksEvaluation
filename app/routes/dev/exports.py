from flask import Blueprint, redirect, url_for, flash, jsonify
import logging

from app.core.tasks import export_charts_task, export_report_task
from app.models import EvaluationHistory


exports_bp = Blueprint('exports', __name__, url_prefix='/dev/export')
logger = logging.getLogger('exports_routes')

@exports_bp.route('/charts', methods=['POST'])
def export_all_charts():
    """
    触发图表导出的celery任务
    """
    logger.info("Chart export requested - triggering celery task.")
    
    try:
        
        task = export_charts_task.delay()
        
        flash(f'图表导出任务已启动（任务ID: {task.id}），请稍后查看 ./exports/imgs/ 文件夹。', 'info')
        logger.info(f"Chart export task queued with ID: {task.id}")
        
    except Exception as e:
        logger.error(f"Error starting chart export task: {e}", exc_info=True)
        flash('启动图表导出任务时发生错误，请检查日志。', 'danger')
    
    return redirect(url_for('index.index'))

@exports_bp.route('/reports', methods=['POST'])
def export_reports():
    """
    触发报告导出的路由
    """
    logger.info("Report export requested.")
    
    try:
        task = export_report_task.delay()
        
        flash(f'报告导出任务已启动（任务ID: {task.id}），请稍后在./exports/reports文件夹中查看结果。', 'info')
        logger.info(f"Report export task queued with ID: {task.id}")
        
    except Exception as e:
        logger.error(f"Error starting report export task: {e}", exc_info=True)
        flash('启动报告导出任务时发生错误，请检查日志。', 'danger')
    
    return redirect(url_for('index.index'))

@exports_bp.route('/history/<int:history_id>', methods=['POST'])
def export_history_report(history_id):
    logger.info(f"Received request to export report of history record {history_id}.")
    
    try:
        history_record = EvaluationHistory.query.get_or_404(history_id)
        timestamp = history_record.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info(f"Successfully get history record {history_id}")
        
    except Exception as e:
        logger.error(f"Failed to get history record {history_id}: {e}", exc_info=True)
        flash('获取历史记录时发生错误，请检查日志。', 'danger')
    
    try:
        task = export_report_task.delay(
            leaderboard_data=(history_record.evaluation_data, history_record.dimensions),
            report_file_name=f"Report of record {timestamp}.md",
            timestamp=history_record.timestamp
        )
        
        flash(f'历史记录报告导出任务已启动（任务ID: {task.id}），请稍后在./exports/reports文件夹中查看结果。', 'info')
        logger.info(f"Report of record {history_id} export task queued with ID: {task.id}")
        
    except Exception as e:
        logger.error(f"Error starting report of record {history_id} export task: {e}", exc_info=True)
        flash('启动历史记录报告导出任务时发生错误，请检查日志。', 'danger')
        
    return redirect(url_for('dev_history.dev_history'))


