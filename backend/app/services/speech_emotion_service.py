import logging
from typing import Optional, Dict
import numpy as np
import torch

from app.core.config import settings
from app.schemas.speech import VocalEmotionResult
from app.services.audio_service import audio_service

logger = logging.getLogger(__name__)

# Official IEMOCAP label mapping verified from SpeechBrain label_encoder.txt
IEMOCAP_LABEL_MAP: Dict[str, str] = {
    "neu": "neutral",
    "hap": "happiness",
    "sad": "sadness",
    "ang": "anger",
    # Fallback mappings in case raw names or indices are returned
    "neutral": "neutral",
    "happiness": "happiness",
    "sadness": "sadness",
    "anger": "anger",
}

INDEX_TO_LABEL: Dict[int, str] = {
    0: "neutral",
    1: "anger",
    2: "happiness",
    3: "sadness",
}


class SpeechEmotionService:
    """
    Singleton service managing SpeechBrain vocal emotion recognition
    using speechbrain/emotion-recognition-wav2vec2-IEMOCAP on CPU.
    """
    _instance: Optional["SpeechEmotionService"] = None

    def __new__(cls) -> "SpeechEmotionService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._classifier = None
            cls._instance._model_source = settings.SPEECHBRAIN_EMOTION_MODEL
            cls._instance._device = settings.SPEECHBRAIN_DEVICE
        return cls._instance

    def _ensure_model_loaded(self) -> None:
        """
        Lazily loads the SpeechBrain foreign_class classifier on first invocation.
        """
        if self._classifier is None:
            try:
                from speechbrain.inference.interfaces import foreign_class
                logger.info(
                    "Loading SpeechBrain emotion model (%s, device: %s)...",
                    self._model_source,
                    self._device,
                )
                self._classifier = foreign_class(
                    source=self._model_source,
                    pymodule_file="custom_interface.py",
                    classname="CustomEncoderWav2vec2Classifier",
                    run_opts={"device": self._device},
                )
                logger.info("SpeechBrain emotion model loaded successfully.")
            except Exception as e:
                logger.error("Failed to load SpeechBrain emotion model: %s", str(e), exc_info=True)
                raise RuntimeError(f"Failed to load SpeechBrain emotion model: {str(e)}") from e

    @property
    def is_loaded(self) -> bool:
        return self._classifier is not None

    def predict_emotion_from_waveform(
        self,
        waveform: np.ndarray,
        sample_rate: int = 16000,
        is_silent: bool = False,
    ) -> VocalEmotionResult:
        """
        Classifies vocal emotion from a normalized 16kHz mono waveform.
        """
        if is_silent:
            return VocalEmotionResult(
                expression=None,
                confidence=0.0,
                all_scores={"neutral": 0.0, "happiness": 0.0, "sadness": 0.0, "anger": 0.0},
            )

        duration = len(waveform) / float(sample_rate)
        if duration < settings.AUDIO_MIN_DURATION_SECONDS:
            return VocalEmotionResult(
                expression=None,
                confidence=0.0,
                all_scores=None,
            )

        temp_wav: Optional[str] = None
        try:
            self._ensure_model_loaded()
            # Write 16kHz audio to clean temporary WAV file for classify_file interface
            temp_wav = audio_service.save_temp_wav(waveform, sample_rate)

            # SpeechBrain returns: out_prob, score, index, text_lab
            out_prob, score, index, text_lab = self._classifier.classify_file(temp_wav)

            # Extract predicted label
            raw_label = text_lab[0] if text_lab and len(text_lab) > 0 else "neu"
            standard_label = IEMOCAP_LABEL_MAP.get(str(raw_label).lower().strip(), "neutral")

            # Extract confidence score
            if isinstance(score, torch.Tensor):
                conf = float(score.item() if score.numel() == 1 else score[0].item())
            else:
                conf = float(score)

            # Extract full probability distribution across the 4 classes
            all_scores: Dict[str, float] = {}
            if isinstance(out_prob, torch.Tensor) and out_prob.numel() >= 4:
                probs = out_prob.squeeze(0).tolist()
                for idx, p in enumerate(probs[:4]):
                    lbl = INDEX_TO_LABEL.get(idx, f"class_{idx}")
                    all_scores[lbl] = round(float(p), 4)

            return VocalEmotionResult(
                expression=standard_label,
                confidence=round(conf, 4),
                all_scores=all_scores if all_scores else None,
            )
        except Exception as e:
            logger.error("SpeechBrain vocal emotion prediction error: %s", str(e), exc_info=True)
            return VocalEmotionResult(
                expression=None,
                confidence=0.0,
                all_scores=None,
            )
        finally:
            if temp_wav:
                audio_service.cleanup_temp_file(temp_wav)


speech_emotion_service = SpeechEmotionService()
