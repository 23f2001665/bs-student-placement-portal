from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3
from argon2 import PasswordHasher
from celery import Celery
from flask_mail import Mail
from flask_cors import CORS

db = SQLAlchemy()
cors = CORS(
    origins=["http://localhost:5173"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Authorization"],
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    )

password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=32 * 1024,  # 32 MB
    parallelism=2,
)

celery = Celery(__name__)
mail = Mail()


@event.listens_for(Engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.fetchone()
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()