"""
Facial Emotion & Engagement Record Database Model for EduSense AI.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

if TYPE_CHECKING:
    from database.models.student import Student


class EmotionRecord(Base):
    __tablename__ = "emotion_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("students.id", ondelete="SET NULL"), index=True, nullable=True)
    session_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(50), nullable=False)  # attentive, confused, neutral, disengaged
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Optional relationship to Student
    student: Mapped[Optional["Student"]] = relationship("Student", backref="emotion_records")

    def __repr__(self) -> str:
        return f"<EmotionRecord(id={self.id}, session_id='{self.session_id}', label='{self.label}', confidence={self.confidence})>"
