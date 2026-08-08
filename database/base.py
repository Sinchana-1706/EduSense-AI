"""
Base Declarative Model for EduSense AI Database Schemas.
"""

from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, Integer


class Base(DeclarativeBase):
    """
    Base class for all future SQLAlchemy database ORM models.
    """
    pass


class TimestampMixin:
    """
    Mixin class providing automatic created_at and updated_at timestamps.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
