from flask import Blueprint, redirect, url_for, flash, jsonify
import logging

# 延迟导入以避免循环依赖
from app.core.tasks import export_charts_task, export_report_task


exports_bp = Blueprint('exports', __name__, url_prefix='/dev/export')
logger = logging.getLogger('exports_routes') # <-- 初始化

@exports_bp.route('/charts', methods=['POST'])
def export_all_charts():
    """
    触发图表导出的celery任务
    """
    logger.info("Chart export requested - triggering celery task.")
    
    try:
        
        # 异步执行图表导出任务
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


