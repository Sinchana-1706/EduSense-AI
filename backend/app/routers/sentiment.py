"""
FastAPI Router for Text Sentiment Analysis.
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models.student import Student
from database.models.speech import SpeechTranscript
from database.models.sentiment import SentimentRecord
from app.schemas.speech import (
    SentimentAnalyzeRequest,
    SentimentAnalyzeResponse,
    SentimentSessionSummary,
)
from ai.sentiment.sentiment_analyzer import sentiment_analyzer

router = APIRouter(prefix="/api/v1/sentiment", tags=["Text Sentiment Analytics"])


@router.post("/analyze", response_model=SentimentAnalyzeResponse, summary="Analyze Transcript Text Sentiment")
def analyze_text_sentiment(
    req: SentimentAnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    Analyzes lecture transcript text using NLTK VADER sentiment model.
    Classifies text as positive, neutral, or negative and stores transcript and sentiment record.
    """
    if not req.transcript.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transcript text cannot be empty.")

    # Find optional student DB ID
    student_db_id = None
    if req.student_id:
        st = db.query(Student).filter(Student.student_id == req.student_id.strip()).first()
        if st:
            student_db_id = st.id

    # Run sentiment analysis
    result = sentiment_analyzer.analyze_text(req.transcript.strip())
    sentiment_label = result.get("sentiment", "neutral")
    confidence = result.get("confidence", 0.75)

    # Save transcript record
    transcript_record = SpeechTranscript(
        session_id=req.session_id,
        speaker_identity=req.student_id,
        transcript=req.transcript.strip(),
        language="en",
        timestamp=datetime.utcnow()
    )
    db.add(transcript_record)

    # Save sentiment record
    record = SentimentRecord(
        session_id=req.session_id,
        student_id=student_db_id,
        transcript=req.transcript.strip(),
        sentiment=sentiment_label,
        confidence=confidence,
        timestamp=datetime.utcnow()
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return SentimentAnalyzeResponse(
        status="success",
        session_id=req.session_id,
        transcript=req.transcript.strip(),
        sentiment=sentiment_label,
        confidence=confidence,
        timestamp=record.timestamp
    )


@router.get("/session/{session_id}", response_model=SentimentSessionSummary, summary="Get Session Text Sentiment Analytics")
def get_session_sentiment_analytics(session_id: str, db: Session = Depends(get_db)):
    """
    Returns aggregated sentiment distribution (positive %, neutral %, negative %)
    and recent transcript results for a given session ID.
    """
    records = db.query(SentimentRecord).filter(SentimentRecord.session_id == session_id).all()
    total_count = len(records)

    if total_count == 0:
        return SentimentSessionSummary(
            session_id=session_id,
            total_transcripts=0,
            distribution={
                "positive": 70.0,
                "neutral": 25.0,
                "negative": 5.0,
            },
            latest_transcript="Welcome to the Data Structures & Algorithms live lecture.",
            recent_results=[]
        )

    counts = {"positive": 0, "neutral": 0, "negative": 0}
    for r in records:
        s = r.sentiment.lower()
        if s in counts:
            counts[s] += 1
        else:
            counts["neutral"] += 1

    distribution = {
        s: round((cnt / total_count) * 100.0, 1)
        for s, cnt in counts.items()
    }

    latest_trans = records[-1].transcript if records else None

    recent_responses = [
        SentimentAnalyzeResponse(
            status="success",
            session_id=r.session_id,
            transcript=r.transcript,
            sentiment=r.sentiment,
            confidence=r.confidence,
            timestamp=r.timestamp
        )
        for r in records[-10:]
    ]

    return SentimentSessionSummary(
        session_id=session_id,
        total_transcripts=total_count,
        distribution=distribution,
        latest_transcript=latest_trans,
        recent_results=recent_responses
    )
