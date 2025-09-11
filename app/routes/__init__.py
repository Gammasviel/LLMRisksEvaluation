from app.routes.dimensions import dimensions_bp
from app.routes.index import index_bp
from app.routes.leaderboard import leaderboard_bp
from app.routes.models import models_bp
from app.routes.settings import settings_bp
from app.routes.questions import questions_bp
from app.routes.public_leaderboard import public_leaderboard_bp
from app.routes.dev_history import dev_history_bp
from app.routes.auth import auth_bp
from app.routes.history import history_bp

__all__ = [
    'dimensions_bp',
    'index_bp',
    'leaderboard_bp',
    'models_bp',
    'settings_bp',
    'questions_bp',
    'public_leaderboard_bp',
    'dev_history_bp',
    'auth_bp', 
    'history_bp'
]