import logging
from flask import Flask
from app.extensions import db, migrate, csrf, icons, login_manager
from flask_uploads import configure_uploads
from app.models import Setting, LLM
from app.core.llm import clients
from app.core.constants import DEFAULT_CRITERIA
from app.routes import blueprints
from app.core.tasks import celery as celery_app

logger = logging.getLogger('main_app')

def register_blueprints(app):
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
        
def initialize():
    
    logger.info("Flask app creation started.")
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_object('app.config')
    app.config.from_pyfile('config.py', silent=True)
    
    configure_uploads(app, icons)
    
    logger.info("Initializing csrf.")
    csrf.init_app(app)

    logger.info("Initializing database.")
    db.init_app(app)
    
    migrate.init_app(app, db)
    
    logger.info("Registering blueprints.")
    register_blueprints(app)
    
    logger.info("Initializing Login Manager.")
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    return app


def create_app():
    app = initialize()
    celery_app.config_from_object(app.config.get('CELERY'))
    celery_app.conf.update(app.config)
    
    with app.app_context():
        logger.info("Creating all database tables.")
        db.create_all()
        
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

