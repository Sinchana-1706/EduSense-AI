"""
Pydantic Schemas for Speech Transcription & Text Sentiment Analysis.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class SpeechTranscribeResponse(BaseModel):
    status: str = "success"
    transcript: str
    language: str
    timestamp: datetime


class SentimentAnalyzeRequest(BaseModel):
    transcript: str = Field(..., description="Transcript text to analyze")
    session_id: str = Field(..., description="Classroom session ID")
    student_id: Optional[str] = Field(None, description="Optional student ID code")


class SentimentAnalyzeResponse(BaseModel):
    status: str = "success"
    session_id: str
    transcript: str
    sentiment: str  # positive, neutral, negative
    confidence: float
    timestamp: datetime


class SentimentSessionSummary(BaseModel):
    session_id: str
    total_transcripts: int
    distribution: Dict[str, float]  # positive %, neutral %, negative %
    latest_transcript: Optional[str] = None
    recent_results: List[SentimentAnalyzeResponse]
