import logging
from app.core.utils import setup_logging
from app import create_app

setup_logging()
logger = logging.getLogger('main_app')

if __name__ == '__main__':
    app = create_app()
    logger.info("Starting Flask development server.")
    app.run(debug=False)