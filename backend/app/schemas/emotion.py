"""
Pydantic Schemas for Facial Emotion & Engagement Analytics.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class EmotionAnalyzeResponse(BaseModel):
    status: str = "success"
    session_id: str
    student_id: Optional[str] = None
    predicted_label: str  # attentive, confused, neutral, disengaged
    confidence: float
    timestamp: datetime


class EmotionSessionSummary(BaseModel):
    session_id: str
    total_samples: int
    distribution: Dict[str, float]  # attentive %, neutral %, confused %, disengaged %
    engagement_percentage: float
    recent_observations: List[EmotionAnalyzeResponse]
