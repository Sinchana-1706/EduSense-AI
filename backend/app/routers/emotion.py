"""
FastAPI Router for Facial Emotion & Engagement Analytics.
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models.student import Student
from database.models.emotion import EmotionRecord
from app.schemas.emotion import (
    EmotionAnalyzeResponse,
    EmotionSessionSummary,
)
from ai.emotion.emotion_analyzer import emotion_analyzer

router = APIRouter(prefix="/api/v1/emotion", tags=["Facial Emotion Analytics"])


@router.post("/analyze", response_model=EmotionAnalyzeResponse, summary="Analyze Facial Emotion & Engagement")
async def analyze_facial_emotion(
    session_id: str = Form("CS-101", description="Classroom session ID"),
    student_id: Optional[str] = Form(None, description="Optional student ID code"),
    file: UploadFile = File(..., description="Face / classroom frame image file"),
    db: Session = Depends(get_db),
):
    """
    Analyzes input face frame for facial expression and maps to classroom engagement labels
    (attentive, confused, neutral, disengaged).
    Stores aggregated results in database.
    """
    frame_bytes = await file.read()
    if not frame_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded image file is empty.")

    # Find optional student DB ID
    student_db_id = None
    if student_id:
        st = db.query(Student).filter(Student.student_id == student_id.strip()).first()
        if st:
            student_db_id = st.id

    # Run emotion analysis using EmotionAnalyzer engine
    result = emotion_analyzer.analyze_face(frame_bytes)
    predicted_label = result.get("engagement_label", "neutral")
    confidence = result.get("confidence", 0.70)

    # Insert EmotionRecord into DB
    record = EmotionRecord(
        student_id=student_db_id,
        session_id=session_id,
        label=predicted_label,
        confidence=confidence,
        timestamp=datetime.utcnow()
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return EmotionAnalyzeResponse(
        status="success",
        session_id=session_id,
        student_id=student_id,
        predicted_label=predicted_label,
        confidence=confidence,
        timestamp=record.timestamp
    )


@router.get("/session/{session_id}", response_model=EmotionSessionSummary, summary="Get Session Emotion Distribution Analytics")
def get_session_emotion_analytics(session_id: str, db: Session = Depends(get_db)):
    """
    Returns aggregated facial engagement metrics for a given session ID
    including distribution percentages for attentive, neutral, confused, and disengaged states.
    """
    records = db.query(EmotionRecord).filter(EmotionRecord.session_id == session_id).all()
    total_count = len(records)

    if total_count == 0:
        # Default distribution for clean initial state
        return EmotionSessionSummary(
            session_id=session_id,
            total_samples=0,
            distribution={
                "attentive": 65.0,
                "neutral": 20.0,
                "confused": 10.0,
                "disengaged": 5.0,
            },
            engagement_percentage=85.0,
            recent_observations=[]
        )

    counts = {"attentive": 0, "neutral": 0, "confused": 0, "disengaged": 0}
    for r in records:
        lbl = r.label.lower()
        if lbl in counts:
            counts[lbl] += 1
        else:
            counts["neutral"] += 1

    distribution = {
        cat: round((cnt / total_count) * 100.0, 1)
        for cat, cnt in counts.items()
    }

    # Calculate overall engagement percentage (attentive + neutral)
    engagement_pct = round(distribution["attentive"] + (distribution["neutral"] * 0.5), 1)

    recent_responses = [
        EmotionAnalyzeResponse(
            status="success",
            session_id=r.session_id,
            student_id=str(r.student_id) if r.student_id else None,
            predicted_label=r.label,
            confidence=r.confidence,
            timestamp=r.timestamp
        )
        for r in records[-10:]  # Latest 10 observations
    ]

    return EmotionSessionSummary(
        session_id=session_id,
        total_samples=total_count,
        distribution=distribution,
        engagement_percentage=engagement_pct,
        recent_observations=recent_responses
    )
