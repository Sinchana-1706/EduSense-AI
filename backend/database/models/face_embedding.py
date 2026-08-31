"""
SQLAlchemy FaceEmbedding database model.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.models.student import Base

if TYPE_CHECKING:
    from database.models.student import Student


class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    embedding: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Optional relationship back to Student model
    student: Mapped["Student"] = relationship("Student", backref="face_embeddings")

    def __repr__(self) -> str:
        return f"<FaceEmbedding(id={self.id}, student_id={self.student_id})>"
