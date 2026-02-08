import sqlite3

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from marshmallow import RAISE, EXCLUDE, INCLUDE
# from marshmallow_sqlalchemy import 
from argon2 import PasswordHasher
from argon2 import exceptions as argon2_exceptions

from sqlalchemy import event
from sqlalchemy.engine import Engine

from flask_migrate import Migrate

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
migrate = Migrate()
ma = Marshmallow()

ma.RAISE = RAISE
ma.EXCLUDE = EXCLUDE
ma.INCLUDE = INCLUDE


password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=64 * 1024,  # 64 MB
    parallelism=2,
)

DUMMY_HASH = password_hasher.hash("DUMMY_PASSWORD_FOR_INVALID_USER")

@event.listens_for(Engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.fetchone()
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

