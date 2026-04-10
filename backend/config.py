import os
from pathlib import Path

from celery import app

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    token = str(raw).strip()
    if token == "":
        return default
    try:
        return int(token)
    except ValueError:
        return default

class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = (
        os.getenv("DATABASE_URI")
        or os.getenv("DATABASE_URL")
        or "sqlite:///database.sqlite3"
    )
    SQLALCHEMY_ECHO = True

    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # Celery
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    CELERY_TASK_DEFAULT_QUEUE = os.getenv("CELERY_TASK_DEFAULT_QUEUE", "ppa")
    CELERY_TIMEZONE = os.getenv("CELERY_TIMEZONE", "Asia/Kolkata")
    CELERY_BEAT_DAILY_DIGEST_HOUR = _env_int("CELERY_BEAT_DAILY_DIGEST_HOUR", 14)
    CELERY_BEAT_DAILY_DIGEST_MINUTE = _env_int("CELERY_BEAT_DAILY_DIGEST_MINUTE", 55)
    CELERY_BEAT_EXPORT_CLEANUP_HOUR = _env_int("CELERY_BEAT_EXPORT_CLEANUP_HOUR", 2)
    CELERY_BEAT_EXPORT_CLEANUP_MINUTE = _env_int("CELERY_BEAT_EXPORT_CLEANUP_MINUTE", 0)
    CELERY_BEAT_MONTHLY_REPORT_CRON = os.getenv("CELERY_BEAT_MONTHLY_REPORT_CRON", "00 22 10 * *")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    ADMIN_REPORT_EMAIL = os.getenv("ADMIN_REPORT_EMAIL")

    # Export temp storage
    EXPORT_TEMP_ROOT = os.getenv("EXPORT_TEMP_ROOT", "temp")
    EXPORT_CLEANUP_RETENTION_HOURS = _env_int("EXPORT_CLEANUP_RETENTION_HOURS", 24)

    # Mail
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEBUG = True

    # CORS
    CORS_ALLOWED_ORIGINS = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173"
    ).split(",")

    CORS_SUPPORTS_CREDENTIALS = True

    # Session
    SECRET_KEY="dev"
    SESSION_COOKIE_SAMESITE="Lax"
    SESSION_COOKIE_SECURE=False
    SESSION_TIMEOUT_SECONDS = _env_int("SESSION_TIMEOUT_SECONDS", 300) # 5 min
    CACHE_TTL_SHORT_SECONDS = _env_int("CACHE_TTL_SHORT_SECONDS", 30)
    CACHE_TTL_LONG_SECONDS = _env_int("CACHE_TTL_LONG_SECONDS", 300)
