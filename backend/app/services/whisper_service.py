import logging
from typing import Optional, Union
import numpy as np

from app.core.config import settings
from app.schemas.speech import TranscriptionResult

logger = logging.getLogger(__name__)


class WhisperService:
    """
    Singleton service managing faster-whisper speech transcription.
    Loads model once and reuses it across requests.
    """
    _instance: Optional["WhisperService"] = None

    def __new__(cls) -> "WhisperService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = None
            cls._instance._model_size = settings.WHISPER_MODEL_SIZE
            cls._instance._device = settings.WHISPER_DEVICE
            cls._instance._compute_type = settings.WHISPER_COMPUTE_TYPE
        return cls._instance

    def _ensure_model_loaded(self) -> None:
        """
        Lazily loads the WhisperModel instance on first invocation.
        """
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info(
                    "Loading faster-whisper model (size: %s, device: %s, compute_type: %s)...",
                    self._model_size,
                    self._device,
                    self._compute_type,
                )
                self._model = WhisperModel(
                    self._model_size,
                    device=self._device,
                    compute_type=self._compute_type,
                )
                logger.info("faster-whisper model loaded successfully.")
            except Exception as e:
                logger.error("Failed to load faster-whisper model: %s", str(e), exc_info=True)
                raise RuntimeError(f"Failed to load faster-whisper model: {str(e)}") from e

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def transcribe(
        self,
        audio: Union[np.ndarray, str],
        duration_seconds: float = 0.0,
        is_silent: bool = False,
    ) -> TranscriptionResult:
        """
        Transcribes a 16kHz mono audio waveform (numpy array) or a file path.

        Args:
            audio: 16kHz float32 mono numpy array or path to an audio file.
            duration_seconds: Total duration of the audio in seconds.
            is_silent: If audio was flagged as silent during pre-analysis.

        Returns:
            TranscriptionResult with text, detected language, and status.
        """
        if is_silent:
            return TranscriptionResult(
                text="",
                language=None,
                language_probability=None,
                duration_seconds=round(duration_seconds, 2),
                status="silent",
            )

        try:
            self._ensure_model_loaded()

            # Pass 1: Transcribe with Silero VAD filtering
            segments, info = self._model.transcribe(
                audio,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=400, speech_pad_ms=200),
            )

            # Collect transcribed text
            segment_texts = [seg.text.strip() for seg in segments if seg.text.strip()]
            full_text = " ".join(segment_texts).strip()

            detected_lang = getattr(info, "language", None)
            lang_prob = getattr(info, "language_probability", None)
            audio_duration = getattr(info, "duration", duration_seconds)

            # Pass 2 Fallback: If VAD filtered everything out but audio had non-trivial signal
            if not full_text and isinstance(audio, np.ndarray) and len(audio) > 0:
                peak_amp = float(np.max(np.abs(audio)))
                if peak_amp >= 0.005:
                    logger.debug("[WhisperService] VAD returned no segments for peak=%.4f; retrying without VAD filter...", peak_amp)
                    try:
                        raw_segments, raw_info = self._model.transcribe(
                            audio,
                            beam_size=3,
                            vad_filter=False,
                        )
                        raw_texts = [s.text.strip() for s in raw_segments if s.text.strip()]
                        raw_full = " ".join(raw_texts).strip()
                        if raw_full:
                            full_text = raw_full
                            detected_lang = getattr(raw_info, "language", detected_lang)
                            lang_prob = getattr(raw_info, "language_probability", lang_prob)
                    except Exception as fallback_err:
                        logger.debug("[WhisperService] Non-VAD fallback warning: %s", fallback_err)

            status = "success" if full_text else "no_speech"

            logger.info(
                "[WhisperService DIAG] Completed: status=%s, lang=%s (prob=%.2f), text='%s'",
                status, detected_lang, float(lang_prob) if lang_prob is not None else 0.0, full_text
            )

            return TranscriptionResult(
                text=full_text,
                language=detected_lang,
                language_probability=round(float(lang_prob), 4) if lang_prob is not None else None,
                duration_seconds=round(float(audio_duration), 2),
                status=status,
                error_message=None,
            )
        except Exception as e:
            logger.error("Whisper transcription error: %s", str(e), exc_info=True)
            return TranscriptionResult(
                text="",
                language=None,
                language_probability=None,
                duration_seconds=round(duration_seconds, 2),
                status="inference_error",
                error_message=str(e),
            )


whisper_service = WhisperService()
