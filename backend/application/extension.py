import sqlite3

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from argon2 import PasswordHasher

from sqlalchemy import event
from sqlalchemy.engine import Engine

from flask_migrate import Migrate

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
migrate = Migrate()

password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=64 * 1024,  # 64 MB
    parallelism=2,
)

@event.listens_for(Engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.fetchone()
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

