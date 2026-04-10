from flask import Flask, current_app
from flask import request
from flask import session
from time import time
from sqlalchemy import select
from .models import User, UserType
from ..config import DevelopmentConfig
from .models import *
from ..extensions import celery, db, cors
from ..tasks.schedules import get_beat_schedule
from .routes import api_bp

def register_blueprints(app, blueprint):
    app.register_blueprint(blueprint)

def create_admin():
    admin_email = str(current_app.config.get("ADMIN_EMAIL") or "").strip()
    admin_password = str(current_app.config.get("ADMIN_PASSWORD") or "")
    if not admin_email:
        raise RuntimeError("ADMIN_EMAIL is required in environment configuration")
    if not admin_password:
        raise RuntimeError("ADMIN_PASSWORD is required in environment configuration")
    existing_admin = db.session.execute(select(User).where(User.email == admin_email)).scalar_one_or_none()
    if not existing_admin:
        admin_user = User(
            name="Admin",
            email=admin_email,
            password=password_hasher.hash(admin_password),
            user_type=UserType.admin,
            is_active=True
        )
        db.session.add(admin_user)
        db.session.commit()

def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)
    session_timeout_seconds = app.config.get("SESSION_TIMEOUT_SECONDS", 300)

    db.init_app(app)
    create_database(app)
    cors.init_app(app)
    init_celery(app)
    register_blueprints(app, api_bp)

    @app.before_request
    def check_timeout():
        # Keep logout idempotent even when session has already expired.
        if request.endpoint == "api.auth.logout_user":
            if session.get("current_user") and session.get("last_active") is None:
                session.clear()
            return None

        current_user_id = session.get("current_user")
        if not current_user_id:
            return None

        now = time()
        last = session.get("last_active")

        # If authenticated session doesn't carry activity timestamp, treat as expired.
        if last is None:
            session.clear()
            return {"error": "Session expired"}, 401

        try:
            if now - float(last) > float(session_timeout_seconds):
                session.clear()
                return {"error": "Session expired"}, 401
        except (TypeError, ValueError):
            session.clear()
            return {"error": "Session expired"}, 401

        session["last_active"] = now

    with app.app_context():
        create_admin()
    return app


def init_celery(app):
    default_queue = app.config.get("CELERY_TASK_DEFAULT_QUEUE", "ppa")
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        task_default_queue=default_queue,
        timezone=app.config.get("CELERY_TIMEZONE", "Asia/Kolkata"),
        task_routes={
            "backend.tasks.*": {"queue": default_queue},
        },
        beat_schedule=get_beat_schedule(app.config),
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask


def create_database(app):
    from sqlalchemy import inspect
    with app.app_context():
        inspector = inspect(db.engine)
        if not inspector.has_table("user"):
            db.drop_all()
            db.create_all()
            return

        # Lightweight compatibility migration for older sqlite DBs.
        if inspector.has_table("drive"):
            drive_columns = {col["name"] for col in inspector.get_columns("drive")}
            if "is_active" not in drive_columns:
                db.session.execute(db.text("ALTER TABLE drive ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1"))
                db.session.commit()

        if inspector.has_table("application"):
            application_columns = {col["name"] for col in inspector.get_columns("application")}
            if "resume_note" not in application_columns:
                db.session.execute(db.text("ALTER TABLE application ADD COLUMN resume_note TEXT"))
                db.session.commit()
            if "resume_link" not in application_columns:
                db.session.execute(db.text("ALTER TABLE application ADD COLUMN resume_link VARCHAR(255)"))
                db.session.commit()

