"""
SQLAlchemy SentimentRecord database model.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.models.student import Base

if TYPE_CHECKING:
    from database.models.student import Student


class SentimentRecord(Base):
    __tablename__ = "sentiment_records"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    session_id: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )

    student_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    transcript: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    sentiment: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    student: Mapped[Optional["Student"]] = relationship("Student", backref="sentiment_records")

    def __repr__(self) -> str:
        return f"<SentimentRecord(id={self.id}, session_id='{self.session_id}', sentiment='{self.sentiment}', confidence={self.confidence})>"
