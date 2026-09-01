"""
Schemas package initialization.
"""

from app.schemas.student import (
    StudentCreate,
    StudentResponse,
    FaceEmbeddingCreate,
    FaceEmbeddingResponse,
    FaceRegistrationRequest,
    FaceRegistrationResponse,
)
from app.schemas.livekit import TokenRequest, TokenResponse
from app.schemas.attendance import (
    AttendanceRecordResponse,
    AttendanceRecognizeResponse,
    AttendanceSessionSummary,
)
from app.schemas.emotion import (
    EmotionAnalyzeResponse,
    EmotionSessionSummary,
)
from app.schemas.speech import (
    SpeechTranscribeResponse,
    SentimentAnalyzeRequest,
    SentimentAnalyzeResponse,
    SentimentSessionSummary,
)
from app.schemas.classroom import (
    ClassroomCreate,
    ClassroomResponse,
    StudentJoinRequest,
    StudentJoinResponse,
)

__all__ = [
    "StudentCreate",
    "StudentResponse",
    "FaceEmbeddingCreate",
    "FaceEmbeddingResponse",
    "FaceRegistrationRequest",
    "FaceRegistrationResponse",
    "TokenRequest",
    "TokenResponse",
    "AttendanceRecordResponse",
    "AttendanceRecognizeResponse",
    "AttendanceSessionSummary",
    "EmotionAnalyzeResponse",
    "EmotionSessionSummary",
    "SpeechTranscribeResponse",
    "SentimentAnalyzeRequest",
    "SentimentAnalyzeResponse",
    "SentimentSessionSummary",
    "ClassroomCreate",
    "ClassroomResponse",
    "StudentJoinRequest",
    "StudentJoinResponse",
]
