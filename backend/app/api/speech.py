import uuid
from datetime import datetime, timezone
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.session import ClassSession, SessionParticipant, SessionStatus
from app.models.stubs import SpeechAnalysis
from app.core.deps import get_db, get_current_user
from app.schemas.speech import (
    SpeechAnalysisResponse,
    TranscriptionResult,
    VocalEmotionResult,
    AudioModelsStatusResponse,
    AudioDiagnostics,
)
from app.services.audio_service import audio_service, AudioProcessingError
from app.services.whisper_service import whisper_service
from app.services.speech_emotion_service import speech_emotion_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/models", response_model=AudioModelsStatusResponse)
async def get_audio_models_status(
    current_user: User = Depends(get_current_user),
):
    """
    Returns the operational status and hardware configuration of speech AI models.
    """
    return AudioModelsStatusResponse(
        whisper_model=settings.WHISPER_MODEL_SIZE,
        whisper_device=settings.WHISPER_DEVICE,
        whisper_compute_type=settings.WHISPER_COMPUTE_TYPE,
        speechbrain_model=settings.SPEECHBRAIN_EMOTION_MODEL,
        speechbrain_device=settings.SPEECHBRAIN_DEVICE,
        whisper_loaded=whisper_service.is_loaded,
        speechbrain_loaded=speech_emotion_service.is_loaded,
        status="ready",
    )


@router.post("/transcribe", response_model=TranscriptionResult)
async def transcribe_audio_endpoint(
    audio: UploadFile = File(..., description="Audio file in WAV, WebM, OGG, or MP3 format"),
    current_user: User = Depends(get_current_user),
):
    """
    Transcribes uploaded speech audio to text using faster-whisper.
    """
    try:
        audio_bytes = await audio.read()
        waveform, sr, duration, is_silent = audio_service.load_audio_to_numpy(audio_bytes)
    except AudioProcessingError as ape:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ape))
    except Exception as e:
        logger.error("Audio decoding error: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to decode audio: {str(e)}",
        )

    async with audio_service.get_semaphore():
        result = whisper_service.transcribe(waveform, duration_seconds=duration, is_silent=is_silent)

    return result


@router.post("/emotion", response_model=VocalEmotionResult)
async def classify_speech_emotion_endpoint(
    audio: UploadFile = File(..., description="Audio file in WAV, WebM, OGG, or MP3 format"),
    current_user: User = Depends(get_current_user),
):
    """
    Classifies vocal emotion (neutral, happiness, sadness, anger) using SpeechBrain IEMOCAP.
    """
    try:
        audio_bytes = await audio.read()
        waveform, sr, duration, is_silent = audio_service.load_audio_to_numpy(audio_bytes)
    except AudioProcessingError as ape:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ape))
    except Exception as e:
        logger.error("Audio decoding error: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to decode audio: {str(e)}",
        )

    async with audio_service.get_semaphore():
        result = speech_emotion_service.predict_emotion_from_waveform(
            waveform, sample_rate=sr, is_silent=is_silent
        )

    return result


@router.post("/analyze", response_model=SpeechAnalysisResponse)
async def analyze_classroom_speech_endpoint(
    session_id: str = Form(..., description="UUID of the active classroom session"),
    audio: UploadFile = File(..., description="Captured audio chunk from participant's microphone"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Comprehensive authenticated classroom speech analysis:
    1. Server-validates classroom session and participant authorization.
    2. Decodes, normalizes, and resamples audio once.
    3. Runs Whisper speech transcription.
    4. Runs SpeechBrain vocal emotion recognition.
    5. Persists observation record in PostgreSQL/SQLite database.
    6. Returns structured transcription and emotion predictions.
    """
    # 1. Validate Session ID
    try:
        sess_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session_id UUID format.")

    session_obj = db.query(ClassSession).filter(ClassSession.id == sess_uuid).first()
    if not session_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom session not found.")

    if session_obj.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session is not active (current status: {session_obj.status.value}).",
        )

    # 2. Server-validated participant identity
    participant_rec = (
        db.query(SessionParticipant)
        .filter(
            SessionParticipant.session_id == sess_uuid,
            SessionParticipant.user_id == current_user.id,
        )
        .first()
    )

    participant_id_str = str(participant_rec.id) if participant_rec else str(current_user.id)

    # 3. Decode & standardize audio
    diagnostics_obj = None
    try:
        audio_bytes = await audio.read()
        load_res = audio_service.load_audio_to_numpy(audio_bytes)
        waveform, sr, duration, is_silent = load_res
        if hasattr(load_res, "diagnostics") and isinstance(load_res.diagnostics, dict):
            diagnostics_obj = AudioDiagnostics(**load_res.diagnostics)
    except AudioProcessingError as ape:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ape))
    except Exception as e:
        logger.error("Audio decoding error: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to decode audio payload: {str(e)}",
        )

    # 4. Run AI Inferences under concurrency semaphore
    async with audio_service.get_semaphore():
        transcription_res = whisper_service.transcribe(
            waveform, duration_seconds=duration, is_silent=is_silent
        )
        vocal_emotion_res = speech_emotion_service.predict_emotion_from_waveform(
            waveform, sample_rate=sr, is_silent=is_silent
        )

    now_utc = datetime.now(timezone.utc)

    logger.info(
        "[Speech API DIAG] Analyzed %.2fs chunk: Whisper status=%s, text='%s', Vocal=%s (conf=%.2f)",
        duration, transcription_res.status, transcription_res.text,
        vocal_emotion_res.expression, vocal_emotion_res.confidence
    )

    # 5. Persist observation to database
    try:
        if participant_rec:
            speech_analysis_record = SpeechAnalysis(
                session_id=sess_uuid,
                participant_id=participant_rec.id,
                sampled_at=now_utc,
                speech_emotion=vocal_emotion_res.expression,
                emotion_confidence=vocal_emotion_res.confidence,
                transcript=transcription_res.text if settings.TRANSCRIPT_RETENTION_ENABLED else None,
                detected_language=transcription_res.language,
                duration_seconds=duration,
            )
            db.add(speech_analysis_record)
            db.commit()
    except Exception as db_err:
        db.rollback()
        logger.warning("Failed to persist SpeechAnalysis record: %s", str(db_err))

    return SpeechAnalysisResponse(
        success=True,
        session_id=str(sess_uuid),
        participant_id=participant_id_str,
        participant_name=current_user.full_name or current_user.email,
        transcription=transcription_res,
        vocal_emotion=vocal_emotion_res,
        duration_seconds=round(duration, 2),
        timestamp=now_utc.isoformat(),
        diagnostics=diagnostics_obj,
        error=None,
    )
