import logging
from flask import Flask
from app.extensions import db, migrate, csrf, icons, login_manager
from flask_uploads import configure_uploads
from app.models import Setting, LLM
from app.core.llm import clients
from app.config import DEFAULT_CRITERIA
from app.routes import dimensions_bp, index_bp, leaderboard_bp, models_bp, questions_bp, settings_bp, public_leaderboard_bp, dev_history_bp, auth_bp, history_bp

logger = logging.getLogger('main_app')

# 2. 创建一个 UploadSet
# 'icons' 是这个集合的名字，IMAGES 是一个预设的包含常见图片扩展名的元组

def register_blueprints(app):
    
    app.register_blueprint(dimensions_bp)
    app.register_blueprint(index_bp)
    app.register_blueprint(leaderboard_bp)
    app.register_blueprint(models_bp)
    app.register_blueprint(questions_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(public_leaderboard_bp)
    app.register_blueprint(dev_history_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(history_bp)

def initialize():
    
    logger.info("Flask app creation started.")
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    
    # logger.info("Configuring uploads.")
    configure_uploads(app, icons)
    
    logger.info("Initializing csrf.")
    csrf.init_app(app)
    
    # logger.info("Initializing login manager.")
    init_login_manager(app)

    logger.info("Initializing database.")
    db.init_app(app)
    
    # logger.info("Migrating database.")
    migrate.init_app(app, db)
    
    logger.info("Registering blueprints.")
    register_blueprints(app)
    
    logger.info("Initializing Login Manager.")
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    return app


def create_app():
    app = initialize()
    
    with app.app_context():
        logger.info("Creating all database tables.")
        db.create_all()
        # import_datas(app)
        
        all_llms = LLM.query.all()
        logger.info(f"Creating LLM clients for {len(all_llms)} models.")
        clients.create_clients([
            {
                'id': llm.id,
                'name': llm.name,
                'model': llm.model,
                'base_url': llm.base_url,
                'api_keys': llm.api_keys,
                'proxy': llm.proxy
            }
            for llm in all_llms
        ])
        
        if Setting.query.first() is None:
            logger.info("No settings found. Creating default settings.")
            default_setting_objective = Setting(question_type = 'objective', criteria=DEFAULT_CRITERIA['objective'])
            default_setting_subjective = Setting(question_type = 'subjective', criteria=DEFAULT_CRITERIA['subjective'])
            db.session.add(default_setting_objective)
            db.session.add(default_setting_subjective)
            db.session.commit()
            logger.info("Default settings created successfully.")
            
    logger.info("Flask app creation finished.")
    return app

