from app.routes.dev.dimensions import dimensions_bp
from app.routes.dev.index import index_bp
from app.routes.dev.leaderboard import leaderboard_bp
from app.routes.dev.models import models_bp
from app.routes.dev.settings import settings_bp
from app.routes.dev.questions import questions_bp
from app.routes.dev.dev_history import dev_history_bp
from app.routes.dev.auth import auth_bp
from app.routes.public.public_leaderboard import public_leaderboard_bp
from app.routes.public.history import history_bp
from app.routes.public.model_detail import model_detail_bp

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
    'history_bp',
    'model_detail_bp'
]