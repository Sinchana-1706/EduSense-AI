"""
SQLAlchemy Models package initialization.
Exports all models so Base.metadata is populated for create_all().
"""

from database.models.student import Base, Student
from database.models.face_embedding import FaceEmbedding
from database.models.attendance import AttendanceRecord
from database.models.emotion import EmotionRecord
from database.models.speech import SpeechTranscript
from database.models.sentiment import SentimentRecord

__all__ = [
    "Base",
    "Student",
    "FaceEmbedding",
    "AttendanceRecord",
    "EmotionRecord",
    "SpeechTranscript",
    "SentimentRecord",
]
