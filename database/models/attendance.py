"""
Attendance Record Database Model for EduSense AI.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

if TYPE_CHECKING:
    from database.models.student import Student


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False)
    session_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    room_name: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PRESENT", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to Student
    student: Mapped["Student"] = relationship("Student", backref="attendance_records")

    def __repr__(self) -> str:
        return f"<AttendanceRecord(id={self.id}, student_id={self.student_id}, session_id='{self.session_id}', status='{self.status}')>"
