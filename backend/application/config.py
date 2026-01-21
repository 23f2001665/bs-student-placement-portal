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

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=10)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=14)
    JWT_CLOCK_SKEW_SECONDS = 30

    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]


    JWT_IDENTITY_CLAIM = "sub"
    JWT_ERROR_MESSAGE_KEY = "error"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///instance/database.sqlite3"
    )

    # JWT_ACCESS_COOKIE_PATH = "/api"
    # JWT_REFRESH_COOKIE_PATH = "/auth"


    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_COOKIE_CSRF_PROTECT = True
    CORS_SUPPORTS_CREDENTIALS = True

    CORS_ALLOWED_ORIGINS = parse_csv(os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:5173"))


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]

    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_SAMESITE = "Strict"
    JWT_COOKIE_CSRF_PROTECT = True
    CORS_SUPPORTS_CREDENTIALS = True

    CORS_ALLOWED_ORIGINS = parse_csv(os.environ.get("CORS_ALLOWED_ORIGINS", "https://yourdomain.com"))
