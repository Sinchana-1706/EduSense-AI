"""
PostgreSQL Database Connection Setup for EduSense AI.
Configures SQLAlchemy engine, session maker, and connection health check helper.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.base import Base
import database.models  # Ensure models are imported for metadata creation

# Read Database URL from environment or use default PostgreSQL connection string
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/edusense_db"
)

# Initialize SQLAlchemy Engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

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
    Helper function to check if PostgreSQL connection is reachable.
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
