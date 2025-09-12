import os

# 基础配置
SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
SQLALCHEMY_DATABASE_URI = 'sqlite:///evaluation.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

CELERY = {
    'broker_url': 'redis://localhost:6379/0',
    'result_backend': 'redis://localhost:6379/0'
}

UPLOADED_ICONS_DEST = 'static/uploads/icons'