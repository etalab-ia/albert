from sqlalchemy.orm import Session

from app.db import base  # noqa: F401
from app.db.create_admin_user import get_or_create_admin_user
from app.db.session import SessionLocal

from pyalbert.config import ENV

# Make sure all SQL Alchemy models are imported (app.db.base) before initializing DB
# otherwise, SQL Alchemy might fail to initialize relationships properly.
# For more details: https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/28


def init_db() -> Session:
    db = SessionLocal()
    if ENV != "unittest":
        get_or_create_admin_user(db)
    return db
