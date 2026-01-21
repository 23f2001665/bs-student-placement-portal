from flask import Flask


from .extension import db, migrate
from .model import *

from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or DevelopmentConfig)
    db.init_app(app)
    migrate.init_app(app, db)
    
    from .user import user_bp
    app.register_blueprint(user_bp)

    return app

from .config import DevelopmentConfig



