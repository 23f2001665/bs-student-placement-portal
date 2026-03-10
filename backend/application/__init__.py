from flask import Flask

from .extensions import *
from .model import *

from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def create_admin(app):
    with app.app_context():
        if not User.query.filter_by(user_type='admin').first():
            admin_user = User(
                user_type='admin', 
                email='admin@mail.com',
                password=password_hasher.hash('Admin@123'),
                name='Admin User',
                is_active=True
                )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created with email:", admin_user.email, "and password: Admin@123")
        else:
            print("Admin user already exists.")


def make_celery(app):

    celery.conf.update(app.config)
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or DevelopmentConfig)
    db.init_app(app)
    migrate.init_app(app, db)
    from flask_cors import CORS

    cors.init_app(app)

    ma.init_app(app)
    jwt.init_app(app)
    make_celery(app)
    mail.init_app(app)
    
    from .public import public_bp
    from .auth import auth_bp
    from .admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)


    create_admin(app)
    return app

from .config import DevelopmentConfig
