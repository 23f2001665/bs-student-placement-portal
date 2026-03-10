# application/config.py
import os
from datetime import timedelta

def parse_csv(value: str):
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]

class BaseConfig:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")

    JWT_ALGORITHM = "HS256"

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=14)
    JWT_CLOCK_SKEW_SECONDS = 30

    JWT_IDENTITY_CLAIM = "sub"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///instance/database.sqlite3"
    )
    SQLALCHEMY_ECHO = False

    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    JWT_TOKEN_LOCATION = ["headers"]
    JWT_COOKIE_SECURE = False

    # mail config
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("EMAIL_USER")
    MAIL_PASSWORD = os.environ.get("EMAIL_PASS")
    MAIL_DEBUG = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]

    JWT_TOKEN_LOCATION = ["cookies", "headers"]
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_SAMESITE = "Strict"
    JWT_COOKIE_CSRF_PROTECT = True
    CORS_SUPPORTS_CREDENTIALS = True

    CORS_ALLOWED_ORIGINS = parse_csv(os.environ.get("CORS_ALLOWED_ORIGINS", "https://yourdomain.com"))
