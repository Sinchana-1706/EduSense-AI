"""
Database Connection Setup for EduSense AI.
Configures SQLAlchemy engine, session maker, and resilient connection fallback.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.base import Base
import database.models  # Ensure models are imported for metadata creation

# Read Database URL from environment or fallback to local SQLite for zero-setup execution
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/edusense_db")
SQLITE_FALLBACK_URL = "sqlite:///./edusense.db"


def _create_db_engine():
    """
    Creates SQLAlchemy engine with automatic fallback to SQLite if PostgreSQL service is offline.
    """
    try:
        if "postgresql" in DATABASE_URL:
            pg_engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
            with pg_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("[DB] Successfully connected to PostgreSQL database.")
            return pg_engine
    except Exception as e:
        print(f"[DB Notice] PostgreSQL connection unavailable ({e}). Falling back to local SQLite database.")

    # SQLite Engine Fallback
    connect_args = {"check_same_thread": False} if "sqlite" in SQLITE_FALLBACK_URL else {}
    sqlite_engine = create_engine(
        SQLITE_FALLBACK_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
        echo=False
    )
    return sqlite_engine


engine = _create_db_engine()

# Configure Session Maker
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    """
    Dependency helper function to obtain database session in FastAPI endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """
    Helper function to check if database connection is reachable.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def init_db():
    """
    Creates all database tables based on SQLAlchemy models.
    """
    Base.metadata.create_all(bind=engine)
