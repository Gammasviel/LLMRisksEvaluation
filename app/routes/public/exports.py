from flask import Blueprint, send_file, current_app, abort
from app.models import EvaluationHistory
from app.core.report_export import ReportExport

public_exports_bp = Blueprint('public_exports', __name__, url_prefix='/public')

@public_exports_bp.route('/export/report/<int:history_id>')
def export_report(history_id):
    """
    Export a report for a given history ID.
    This is a synchronous version for direct download.
    """
    if not EvaluationHistory.query.get(history_id):
        return abort(404)

    try:
        report_path = ReportExport.generate_export_file(history_id)
        return send_file(report_path, as_attachment=True)
    except Exception as e:
        current_app.logger.error(f"Error exporting report for history_id {history_id}: {e}")
        return "Error generating report.", 500

@public_exports_bp.route('/export/leaderboard')
def export_leaderboard():
    """
    Export the current leaderboard report.
    """
    try:
        report_path = ReportExport.generate_current_leaderboard_export()
        return send_file(report_path, as_attachment=True)
    except Exception as e:
        current_app.logger.error(f"Error exporting leaderboard report: {e}", exc_info=True)
        return "Error generating report.", 500
