from flask import Blueprint, send_file, current_app, abort, redirect, url_for, flash
from app.models import EvaluationHistory, Question
from app.core.report_export import export_report
from app.core.utils import convert_markdown_to_pdf, generate_leaderboard_data
from app.extensions import db
from pathlib import Path

public_exports_bp = Blueprint('public_exports', __name__, url_prefix='/public')

@public_exports_bp.route('/export/report/<int:history_id>')
def export_report_history(history_id):
    """
    Export a report for a given history ID.
    This is a synchronous version for direct download.
    """
    try:
        from app.core.report_export import get_or_generate_report
        pdf_path = get_or_generate_report(history_id)
        if pdf_path:
            return send_file(pdf_path, as_attachment=True)
        else:
            flash('Failed to generate PDF report.', 'danger')
            return redirect(url_for('public_history.history_detail', history_id=history_id))

    except Exception as e:
        current_app.logger.error(f"Error exporting report for history_id {history_id}: {e}")
        flash("Error generating report.", 'danger')
        return redirect(url_for('public_history.history_detail', history_id=history_id))

@public_exports_bp.route('/export/leaderboard')
def export_leaderboard():
    """
    Export the current leaderboard report by always generating a new one.
    """
    try:
        current_data = generate_leaderboard_data()
        total_questions = Question.query.count()

        history_record = EvaluationHistory(
            dimensions=current_data['l1_dimensions'],
            evaluation_data=current_data['leaderboard'],
            extra_info={
                'total_models': len(current_data['leaderboard']),
                'total_dimensions': len(current_data['l1_dimensions']),
                'total_questions': total_questions,
                'manual_save': True,
                'source': 'public_export'
            }
        )
        db.session.add(history_record)
        db.session.commit()

        markdown_path_str = export_report(
            leaderboard_data=[history_record.evaluation_data, history_record.dimensions],
            report_file_name=f"Report-{history_record.id}.md",
            timestamp=history_record.timestamp
        )
        history_record.markdown_report_path = markdown_path_str
        db.session.commit()

        pdf_path = Path(markdown_path_str).with_suffix('.pdf')
        if convert_markdown_to_pdf(markdown_path_str, str(pdf_path)):
            history_record.pdf_report_path = str(pdf_path)
            db.session.commit()
            return send_file(str(pdf_path), as_attachment=True)
        else:
            flash('Failed to convert report to PDF.', 'danger')
            return redirect(url_for('public_leaderboard.display_public_leaderboard'))

    except Exception as e:
        current_app.logger.error(f"Error exporting leaderboard report: {e}", exc_info=True)
        flash("Error generating report.", 'danger')
        return redirect(url_for('public_leaderboard.display_public_leaderboard'))