"""
Face Embedding Database Model for EduSense AI.
"""

from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

if TYPE_CHECKING:
    from database.models.student import Student


class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False)
    embedding: Mapped[List[float]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship back to Student
    student: Mapped["Student"] = relationship("Student", back_populates="embeddings")

    def __repr__(self) -> str:
        return f"<FaceEmbedding(id={self.id}, student_id={self.student_id})>"
