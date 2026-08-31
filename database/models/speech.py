"""
Speech Transcript Database Model for EduSense AI.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base


class SpeechTranscript(Base):
    __tablename__ = "speech_transcripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    speaker_identity: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<SpeechTranscript(id={self.id}, session_id='{self.session_id}', transcript='{self.transcript[:30]}...')>"
