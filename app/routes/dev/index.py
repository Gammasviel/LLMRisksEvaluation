from flask import Blueprint, render_template
import logging
from app.routes.dev.auth import admin_required
from flask_login import login_required

index_bp = Blueprint('index', __name__)
logger = logging.getLogger('index_routes')

@index_bp.route('/dev')
@index_bp.route('/dev/index')
@login_required
@admin_required
def index():
    logger.info("Main index page accessed.")
    return render_template('dev/index.html')