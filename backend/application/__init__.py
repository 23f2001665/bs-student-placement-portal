from flask import Flask

from .extension import db, migrate, ma, jwt, password_hasher
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

    

def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or DevelopmentConfig)
    db.init_app(app)
    migrate.init_app(app, db)
    from flask_cors import CORS

    CORS(
        app,
        resources={r"/auth/*": {"origins": "http://localhost:5173"}},
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Authorization"],
        supports_credentials=True,
    )

    ma.init_app(app)
    jwt.init_app(app)
    
    from .public import public_bp
    from .auth import auth_bp
    from .admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    create_admin(app)
    return app

from .config import DevelopmentConfig
