from flask import Blueprint, redirect, url_for, flash
import logging

# 延迟导入以避免循环依赖
from app.core.tasks import export_charts_task
from app.core.report_export import export_report


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
        
        flash(f'图表导出任务已启动（任务ID: {task.id}），请稍后查看 ./temp/imgs/ 文件夹。', 'info')
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
        export_report()
        flash('报告已成功导出。', 'success')
        logger.info("Report exported successfully.")
        
    except Exception as e:
        logger.error(f"Error exporting report: {e}", exc_info=True)
        flash('导出报告时发生错误，请检查日志。', 'danger')
    
    return redirect(url_for('index.index'))


