import logging
from flask import Blueprint, render_template, flash, redirect, url_for, request
from models import EvaluationHistory

logger = logging.getLogger('history_routes')
history_bp = Blueprint('history', __name__, url_prefix='/history')

@history_bp.route('/')
def evaluation_history():
    """显示历史评估记录"""
    logger.info("Accessing evaluation history page.")
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        query = EvaluationHistory.query
        if start_date:
            try:
                from datetime import datetime
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(EvaluationHistory.timestamp >= start_dt)
            except ValueError:
                flash('起始日期格式无效，请使用 YYYY-MM-DD 格式', 'warning')
        if end_date:
            try:
                from datetime import datetime
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(EvaluationHistory.timestamp <= end_dt)
            except ValueError:
                flash('结束日期格式无效，请使用 YYYY-MM-DD 格式', 'warning')
        history_records = query.order_by(EvaluationHistory.timestamp.desc()).all()
        return render_template('evaluation_history.html', 
                             history_records=history_records,
                             start_date=start_date,
                             end_date=end_date)
    except Exception as e:
        logger.error(f"Error loading evaluation history: {e}", exc_info=True)
        flash('加载历史记录时发生错误，请检查日志。', 'danger')
        return render_template('evaluation_history.html', 
                             history_records=[],
                             start_date=None,
                             end_date=None)

@history_bp.route('/<int:history_id>')
def history_detail(history_id):
    """显示特定历史记录的详细数据"""
    logger.info(f"Accessing history detail for record {history_id}.")
    try:
        history_record = EvaluationHistory.query.get_or_404(history_id)
        sort_by = request.args.get('sort_by', 'avg_score')
        sort_order = request.args.get('sort_order', 'desc')
        leaderboard_data = history_record.evaluation_data
        reverse = sort_order == 'desc'
        if sort_by.startswith('dim_'):
            dim_id = sort_by.split('_')[1]
            leaderboard_data.sort(key=lambda x: x['dim_scores_display'].get(dim_id, -1), reverse=reverse)
        else:
            leaderboard_data.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)

        # Prepare data for charts
        charts_data = {}
        dim_labels = [dim['name'] for dim in history_record.dimensions]
        for model_data in leaderboard_data:
            model_name = model_data['name']
            dim_scores = model_data.get('dim_scores', {})
            
            response_rates = []
            avg_scores = []
            
            for dim in history_record.dimensions:
                dim_id_int = dim['id']
                dim_id_str = str(dim['id'])
                # Check both integer and string keys for robustness
                score_info = dim_scores.get(dim_id_str) or dim_scores.get(dim_id_int) or {}
                response_rates.append(score_info.get('response_rate', 0))
                avg_scores.append(score_info.get('avg', 0))

            charts_data[model_name] = {
                'response_rate_by_dimension': {
                    'labels': dim_labels,
                    'datasets': [{'label': '响应率 (%)', 'data': response_rates, 'backgroundColor': 'rgba(75, 192, 192, 0.6)'}]
                },
                'avg_scores_by_dimension': {
                    'labels': dim_labels,
                    'datasets': [{'label': '平均得分', 'data': avg_scores, 'backgroundColor': 'rgba(153, 102, 255, 0.6)'}]
                }
                # NOTE: Bias analysis chart cannot be generated as raw data is not stored in history.
            }

        return render_template('history_detail.html',
                             history_record=history_record,
                             leaderboard=leaderboard_data,
                             l1_dimensions=history_record.dimensions,
                             score_threshold=history_record.extra_info.get('score_threshold', 3.0),
                             rate_threshold=history_record.extra_info.get('rate_threshold', 90.0),
                             current_sort_by=sort_by,
                             current_sort_order=sort_order,
                             charts_data=charts_data)
    except Exception as e:
        logger.error(f"Error loading history detail {history_id}: {e}", exc_info=True)
        flash('加载历史记录详情时发生错误。', 'danger')
        return redirect(url_for('history.evaluation_history'))
