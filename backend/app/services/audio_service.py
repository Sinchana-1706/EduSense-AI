import logging
import io
import os
import tempfile
import asyncio
from typing import Tuple, Optional, Dict, Any
import numpy as np
import soundfile as sf
import torch
import torchaudio

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global concurrency limiter: maximum 2 simultaneous heavy audio inference tasks on CPU
_INFERENCE_SEMAPHORE = asyncio.Semaphore(2)


class AudioProcessingError(Exception):
    """Custom exception for audio validation and decoding failures."""
    pass


class AudioLoadResult(tuple):
    """
    Subclass of tuple returning (waveform, sr, duration, is_silent) for backward
    compatibility, while attaching rich .diagnostics dictionary and named fields.
    """
    def __new__(cls, waveform: np.ndarray, sample_rate: int, duration: float, is_silent: bool, diagnostics: Dict[str, Any]):
        obj = super().__new__(cls, (waveform, sample_rate, duration, is_silent))
        obj.waveform = waveform
        obj.sample_rate = sample_rate
        obj.duration = duration
        obj.is_silent = is_silent
        obj.diagnostics = diagnostics
        return obj


class AudioService:
    """
    Shared, reusable audio processing service for Whisper transcription
    and SpeechBrain vocal emotion analysis.
    """

    TARGET_SAMPLE_RATE: int = 16000
    # True digital silence noise floor threshold (-86 dBFS)
    SILENCE_RMS_THRESHOLD: float = 0.00005
    SILENCE_PEAK_THRESHOLD: float = 0.0005

    @staticmethod
    def get_semaphore() -> asyncio.Semaphore:
        return _INFERENCE_SEMAPHORE

    @classmethod
    def validate_audio_bytes(cls, audio_bytes: bytes) -> None:
        """
        Validates audio file size against configured limits.
        """
        if not audio_bytes or len(audio_bytes) == 0:
            raise AudioProcessingError("Audio payload is empty.")

        max_bytes = settings.AUDIO_MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(audio_bytes) > max_bytes:
            raise AudioProcessingError(
                f"Audio payload size ({len(audio_bytes) / 1024 / 1024:.2f} MB) exceeds maximum limit "
                f"of {settings.AUDIO_MAX_UPLOAD_SIZE_MB} MB."
            )

    @classmethod
    def load_audio_to_numpy(cls, audio_bytes: bytes) -> Tuple[np.ndarray, int, float, bool]:
        """
        Decodes any supported audio format (WAV, WebM, OGG, MP3, FLAC) into a
        standardized mono float32 numpy array at 16,000 Hz.

        Returns:
            Tuple of (waveform_16k, sample_rate, duration_seconds, is_silent)
        """
        cls.validate_audio_bytes(audio_bytes)

        waveform: Optional[np.ndarray] = None
        sr: int = cls.TARGET_SAMPLE_RATE

        # 1. Attempt fast decoding with soundfile (supports WAV, FLAC, OGG)
        try:
            with io.BytesIO(audio_bytes) as bio:
                data, in_sr = sf.read(bio, dtype='float32')
                # Convert multi-channel to mono
                if data.ndim > 1:
                    data = np.mean(data, axis=1)
                waveform = data
                sr = in_sr
        except Exception:
            waveform = None

        # 2. Fall back to PyAV container decoding (supports WebM/Opus, MP3, etc.)
        if waveform is None:
            try:
                import av
                with io.BytesIO(audio_bytes) as bio:
                    container = av.open(bio)
                    resampler = av.AudioResampler(format='fltp', layout='mono', rate=cls.TARGET_SAMPLE_RATE)
                    resampled_chunks = []
                    for frame in container.decode(audio=0):
                        frame.pts = None
                        for rf in resampler.resample(frame):
                            resampled_chunks.append(rf.to_ndarray())
                    if resampled_chunks:
                        waveform = np.concatenate(resampled_chunks, axis=1).squeeze(0).astype(np.float32)
                        sr = cls.TARGET_SAMPLE_RATE
            except Exception as av_err:
                raise AudioProcessingError(
                    f"Failed to decode audio payload with soundfile or PyAV: {str(av_err)}"
                ) from av_err

        if waveform is None or len(waveform) == 0:
            raise AudioProcessingError("Decoded audio waveform is empty or corrupted.")

        # 3. Resample to 16,000 Hz if needed
        if sr != cls.TARGET_SAMPLE_RATE:
            tensor_wave = torch.from_numpy(waveform).unsqueeze(0)
            resampled_tensor = torchaudio.functional.resample(tensor_wave, sr, cls.TARGET_SAMPLE_RATE)
            waveform = resampled_tensor.squeeze(0).numpy().astype(np.float32)
            sr = cls.TARGET_SAMPLE_RATE

        duration = len(waveform) / float(cls.TARGET_SAMPLE_RATE)

        # 4. Check duration boundaries
        if duration < settings.AUDIO_MIN_DURATION_SECONDS:
            raise AudioProcessingError(
                f"Audio duration ({duration:.2f}s) is shorter than minimum supported "
                f"duration ({settings.AUDIO_MIN_DURATION_SECONDS:.2f}s)."
            )

        if duration > settings.AUDIO_MAX_DURATION_SECONDS:
            raise AudioProcessingError(
                f"Audio duration ({duration:.2f}s) exceeds maximum supported "
                f"duration ({settings.AUDIO_MAX_DURATION_SECONDS:.2f}s)."
            )

        # 5. Peak normalization
        peak_amp = float(np.max(np.abs(waveform)))
        if peak_amp > 1.0:
            waveform = waveform / peak_amp
            peak_amp = 1.0

        # 6. Check for true silence or zero signal
        rms_amp = float(np.sqrt(np.mean(waveform ** 2)))
        is_all_zeros = bool(peak_amp == 0.0)
        is_silent = bool(is_all_zeros or (peak_amp < cls.SILENCE_PEAK_THRESHOLD and rms_amp < cls.SILENCE_RMS_THRESHOLD))

        diagnostics = {
            "byte_size": len(audio_bytes),
            "sample_rate": sr,
            "channel_count": 1,
            "sample_count": len(waveform),
            "duration_seconds": round(duration, 3),
            "peak_amplitude": round(peak_amp, 6),
            "rms_amplitude": round(rms_amp, 6),
            "is_all_zeros": is_all_zeros,
            "is_silent": is_silent,
        }

        logger.info(
            "[AudioService DIAG] Decoded payload: %d B, sr=%d, dur=%.2fs, samples=%d, peak=%.6f, rms=%.6f, zeros=%s, silent=%s",
            len(audio_bytes), sr, duration, len(waveform), peak_amp, rms_amp, is_all_zeros, is_silent
        )

        return AudioLoadResult(waveform, sr, duration, is_silent, diagnostics)

    @classmethod
    def save_temp_wav(cls, waveform: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Saves a float32 mono waveform to a temporary standard WAV file on disk.
        Caller is responsible for removing the file when done.
        """
        temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')
        os.close(temp_fd)
        try:
            sf.write(temp_path, waveform, sample_rate, subtype='PCM_16')
            return temp_path
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise AudioProcessingError(f"Failed to write temporary WAV file: {str(e)}") from e

    @staticmethod
    def cleanup_temp_file(file_path: Optional[str]) -> None:
        """
        Safely removes a temporary file from disk.
        """
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass


audio_service = AudioService()
