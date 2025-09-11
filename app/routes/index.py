# .\routes\index.py

from flask import Blueprint, render_template, flash, redirect, url_for, request
import logging
from app.routes.auth import admin_required
from flask_login import login_required

index_bp = Blueprint('index', __name__)
logger = logging.getLogger('index_routes') # <-- 初始化

@index_bp.route('/dev')
@index_bp.route('/dev/index')
@login_required
@admin_required
def index():
    logger.info("Main index page accessed.") # <-- 添加日志
    return render_template('index.html')

@index_bp.route('/dev/export-charts', methods=['POST'])
@login_required
@admin_required
def export_all_charts():
    """
    触发图表导出的celery任务
    """
    logger.info("Chart export requested - triggering celery task.")
    
    try:
        # 延迟导入以避免循环依赖
        from tasks import export_charts_task
        
        # 异步执行图表导出任务
        task = export_charts_task.delay()
        
        flash(f'图表导出任务已启动（任务ID: {task.id}），请稍后查看 ./temp/imgs/ 文件夹。', 'info')
        logger.info(f"Chart export task queued with ID: {task.id}")
        
    except Exception as e:
        logger.error(f"Error starting chart export task: {e}", exc_info=True)
        flash('启动图表导出任务时发生错误，请检查日志。', 'danger')
    
    return redirect(url_for('index.index'))

