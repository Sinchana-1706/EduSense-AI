import uuid
from typing import Dict, Optional
from pydantic import BaseModel, Field


class VocalEmotionResult(BaseModel):
    """
    Structured vocal emotion classification result from SpeechBrain.
    """
    expression: Optional[str] = Field(
        None,
        description="Classified emotion label: neutral, happiness, sadness, or anger"
    )
    confidence: float = Field(
        0.0,
        description="Softmax probability score of the dominant emotion (0.0 to 1.0)"
    )
    all_scores: Optional[Dict[str, float]] = Field(
        default=None,
        description="Probability distribution across all recognized emotion classes"
    )


class AudioDiagnostics(BaseModel):
    """
    Sanitized audio hardware and payload diagnostics for developer inspection.
    """
    byte_size: int = Field(..., description="Uploaded audio chunk byte size")
    duration_seconds: float = Field(..., description="Duration in seconds")
    sample_rate: int = Field(..., description="Sample rate in Hz")
    channel_count: int = Field(1, description="Number of audio channels")
    sample_count: int = Field(..., description="PCM float32 sample count")
    peak_amplitude: float = Field(..., description="Peak absolute sample amplitude (0.0 to 1.0)")
    rms_amplitude: float = Field(..., description="Root-mean-square amplitude")
    is_all_zeros: bool = Field(..., description="True if payload is pure zeroes")
    is_silent: bool = Field(..., description="True if payload is digital silence")


class TranscriptionResult(BaseModel):
    """
    Structured transcription output from faster-whisper.
    """
    text: str = Field(
        "",
        description="Transcribed text from speech"
    )
    language: Optional[str] = Field(
        None,
        description="Detected language code (e.g., 'en', 'es', 'fr')"
    )
    language_probability: Optional[float] = Field(
        None,
        description="Probability score for detected language (0.0 to 1.0)"
    )
    duration_seconds: float = Field(
        0.0,
        description="Audio duration in seconds"
    )
    status: str = Field(
        "success",
        description="Transcription status: 'success', 'no_speech', 'silent', 'invalid_audio', 'auth_error', 'inference_error'"
    )
    error_message: Optional[str] = Field(
        None,
        description="Detailed error message if transcription failed"
    )


class SpeechAnalysisResponse(BaseModel):
    """
    Combined real-time audio analysis response containing both speech-to-text
    and vocal emotion recognition results.
    """
    success: bool
    session_id: str
    participant_id: str
    participant_name: str
    transcription: TranscriptionResult
    vocal_emotion: Optional[VocalEmotionResult] = None
    duration_seconds: float
    timestamp: str
    diagnostics: Optional[AudioDiagnostics] = None
    error: Optional[str] = None


class AudioModelsStatusResponse(BaseModel):
    """
    Status report of loaded speech models.
    """
    whisper_model: str
    whisper_device: str
    whisper_compute_type: str
    speechbrain_model: str
    speechbrain_device: str
    whisper_loaded: bool
    speechbrain_loaded: bool
    status: str
