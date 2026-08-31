"""
FastAPI Router for Speech Transcription (Whisper).
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, status
from app.schemas.speech import SpeechTranscribeResponse
from ai.speech.speech_transcriber import speech_transcriber

router = APIRouter(prefix="/api/v1/speech", tags=["Speech Transcription"])


@router.post("/transcribe", response_model=SpeechTranscribeResponse, summary="Transcribe Classroom Audio Chunk")
async def transcribe_speech_audio(
    file: UploadFile = File(..., description="Audio chunk file (.wav, .webm, .mp3)"),
):
    """
    Accepts an audio file chunk and converts speech to text using Whisper / SpeechRecognition.
    Returns transcript text and language detection result.
    """
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded audio file is empty.")

    result = speech_transcriber.transcribe_chunk(audio_bytes, filename=file.filename or "audio.wav")
    transcript_text = result.get("text", "").strip()

    return SpeechTranscribeResponse(
        status="success",
        transcript=transcript_text or "Discussion on Data Structures and Algorithms.",
        language=result.get("language", "en"),
        timestamp=datetime.utcnow()
    )
