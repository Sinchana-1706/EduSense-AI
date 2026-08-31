"""
SQLAlchemy database connection and session management with resilient fallback.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from database.models.student import Base
import database.models  # Ensures all models are registered on Base.metadata


def _create_db_engine():
    """
    Creates SQLAlchemy engine with automatic fallback to SQLite if PostgreSQL service is offline.
    """
    db_url = getattr(settings, "DATABASE_URL", None) or os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/edusense_db"
    )

    try:
        if "postgresql" in db_url:
            pg_engine = create_engine(db_url, pool_pre_ping=True, echo=False)
            with pg_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("[DB] Successfully connected to PostgreSQL database.")
            return pg_engine
    except Exception as e:
        err_msg = str(e).encode("ascii", "ignore").decode("ascii")
        print(f"[DB Notice] PostgreSQL unavailable ({err_msg}). Falling back to local SQLite database.")

    sqlite_url = "sqlite:///./edusense.db"
    connect_args = {"check_same_thread": False}
    return create_engine(
        sqlite_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        echo=False,
    )


engine = _create_db_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def init_db():
    """
    Initialize the database and create all registered tables.
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Provides a database session for FastAPI requests.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()