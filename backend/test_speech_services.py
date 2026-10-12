"""
test_speech_services.py
Automated Unit and Integration Test Suite for Phase 4: Whisper + SpeechBrain Integration.
"""
import io
import os
import uuid
import wave
import struct
import numpy as np
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.classroom import Classroom
from app.models.session import ClassSession, SessionParticipant, SessionStatus
from app.models.stubs import SpeechAnalysis
from app.services.audio_service import audio_service, AudioProcessingError
from app.services.whisper_service import whisper_service
from app.services.speech_emotion_service import speech_emotion_service, IEMOCAP_LABEL_MAP
from app.core.security import create_access_token


def generate_wav_bytes(duration_sec: float = 2.0, freq: float = 440.0, sample_rate: int = 16000, amplitude: float = 0.5) -> bytes:
    """Helper: Generates standard 16kHz mono 16-bit PCM WAV in memory."""
    num_samples = int(duration_sec * sample_rate)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_samples):
            val = int(amplitude * 32767.0 * np.sin(2.0 * np.pi * freq * (i / sample_rate)))
            frames.extend(struct.pack('<h', max(-32768, min(32767, val))))
        wf.writeframes(frames)
    return buf.getvalue()


def test_audio_service_validation():
    print("\n--- TEST 1: AudioService Format & Bounds Validation ---")
    # Empty audio
    caught_empty = False
    try:
        audio_service.load_audio_to_numpy(b"")
    except AudioProcessingError:
        caught_empty = True
    assert caught_empty, "Should raise AudioProcessingError on empty bytes"

    # Short audio (< 0.5s)
    short_wav = generate_wav_bytes(duration_sec=0.2)
    caught_short = False
    try:
        audio_service.load_audio_to_numpy(short_wav)
    except AudioProcessingError:
        caught_short = True
    assert caught_short, "Should raise AudioProcessingError on audio < 0.5s"

    # Valid audio decoding and resampling
    valid_wav = generate_wav_bytes(duration_sec=1.5, sample_rate=16000)
    waveform, sr, duration, is_silent = audio_service.load_audio_to_numpy(valid_wav)
    assert sr == 16000, f"Expected 16000 sr, got {sr}"
    assert 1.4 <= duration <= 1.6, f"Expected ~1.5s, got {duration}"
    assert not is_silent, "Tone should not be silent"
    assert isinstance(waveform, np.ndarray)
    print("PASS: AudioService validation & bounds checks passed.")


def test_audio_service_silence_detection():
    print("\n--- TEST 2: AudioService Silence Detection ---")
    silent_wav = generate_wav_bytes(duration_sec=1.0, amplitude=0.0)
    waveform, sr, duration, is_silent = audio_service.load_audio_to_numpy(silent_wav)
    assert is_silent, "Zero amplitude audio should be detected as silent"
    print("PASS: Silence detection passed.")


def test_whisper_service_smoke():
    print("\n--- TEST 3: WhisperService Real Inference Smoke Test ---")
    wav_bytes = generate_wav_bytes(duration_sec=1.5)
    waveform, sr, duration, is_silent = audio_service.load_audio_to_numpy(wav_bytes)

    result = whisper_service.transcribe(waveform, duration_seconds=duration, is_silent=is_silent)
    assert result.status in ["success", "no_speech"], f"Unexpected status: {result.status}"
    assert result.duration_seconds > 0
    print(f"PASS: Whisper transcribed test audio (status='{result.status}', lang='{result.language}')")


def test_speechbrain_emotion_smoke():
    print("\n--- TEST 4: SpeechBrain Emotion Real Inference Smoke Test ---")
    wav_bytes = generate_wav_bytes(duration_sec=2.0, freq=300.0)
    waveform, sr, duration, is_silent = audio_service.load_audio_to_numpy(wav_bytes)

    result = speech_emotion_service.predict_emotion_from_waveform(waveform, sample_rate=sr, is_silent=is_silent)
    assert result.expression in ["neutral", "happiness", "sadness", "anger"], f"Invalid emotion: {result.expression}"
    assert 0.0 <= result.confidence <= 1.0, f"Confidence out of bounds: {result.confidence}"
    if result.all_scores:
        assert "neutral" in result.all_scores
        assert "happiness" in result.all_scores
    print(f"PASS: SpeechBrain predicted vocal emotion: '{result.expression}' (conf: {result.confidence:.2f})")


def test_api_speech_endpoints():
    print("\n--- TEST 5: Authenticated API Speech Endpoints ---")
    db = SessionLocal()
    client = TestClient(app)

    try:
        # Create test instructor & student
        test_uid = uuid.uuid4().hex[:6]
        user = User(
            email=f"speech_test_{test_uid}@edusense.ai",
            password_hash="testpasshash",
            full_name="Speech Test Student",
            role=UserRole.STUDENT,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        teacher_user = User(
            email=f"teacher_{test_uid}@edusense.ai",
            password_hash="testpasshash",
            full_name="Prof. Audio",
            role=UserRole.TEACHER,
            is_active=True,
        )
        db.add(teacher_user)
        db.commit()
        db.refresh(teacher_user)

        from app.models.profile import TeacherProfile
        teacher_prof = TeacherProfile(user_id=teacher_user.id, employee_id=f"EMP_{test_uid}")
        db.add(teacher_prof)
        db.commit()
        db.refresh(teacher_prof)

        classroom = Classroom(
            title=f"Speech Test Room {test_uid}",
            course_code=f"AUD_{test_uid.upper()}",
            teacher_id=teacher_prof.id,
            livekit_room_name=f"room_speech_{test_uid}",
            is_active=True,
        )
        db.add(classroom)
        db.commit()
        db.refresh(classroom)

        from datetime import timedelta
        now_utc = datetime.now(timezone.utc)
        session = ClassSession(
            classroom_id=classroom.id,
            title=f"Live Speech Session {test_uid}",
            status=SessionStatus.ACTIVE,
            scheduled_start_time=now_utc,
            scheduled_end_time=now_utc + timedelta(hours=1),
            actual_start_time=now_utc,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        participant = SessionParticipant(
            session_id=session.id,
            user_id=user.id,
            role="STUDENT",
            joined_at=now_utc,
        )
        db.add(participant)
        db.commit()
        db.refresh(participant)

        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # 1. GET /api/speech/models
        resp_models = client.get("/api/speech/models", headers=headers)
        assert resp_models.status_code == 200, f"Models status failed: {resp_models.text}"
        m_data = resp_models.json()
        assert m_data["status"] == "ready"
        assert m_data["whisper_model"] == settings.WHISPER_MODEL_SIZE
        print("PASS: GET /api/speech/models returned 200 ready.")

        # 2. POST /api/speech/analyze
        test_wav = generate_wav_bytes(duration_sec=2.0)
        files = {"audio": ("test_audio.wav", test_wav, "audio/wav")}
        data = {"session_id": str(session.id)}

        resp_analyze = client.post("/api/speech/analyze", headers=headers, data=data, files=files)
        assert resp_analyze.status_code == 200, f"Analyze failed: {resp_analyze.text}"
        res_json = resp_analyze.json()
        assert res_json["success"] is True
        assert res_json["participant_name"] == "Speech Test Student"
        assert "transcription" in res_json
        assert "vocal_emotion" in res_json
        assert res_json["vocal_emotion"]["expression"] in ["neutral", "happiness", "sadness", "anger"]
        print(f"PASS: POST /api/speech/analyze returned success=True (vocal_emotion: {res_json['vocal_emotion']['expression']})")

        # 3. Verify database persistence in speech_analyses
        saved_rec = db.query(SpeechAnalysis).filter(
            SpeechAnalysis.session_id == session.id,
            SpeechAnalysis.participant_id == participant.id,
        ).first()
        assert saved_rec is not None, "SpeechAnalysis record was not saved in DB"
        assert saved_rec.speech_emotion == res_json["vocal_emotion"]["expression"]
        print("PASS: SpeechAnalysis record confirmed in database table.")

        # 4. Unauthorized rejection check
        resp_no_auth = client.get("/api/speech/models")
        assert resp_no_auth.status_code == 401, "Expected 401 Unauthorized without token"
        print("PASS: Authentication guard verified.")

    finally:
        db.close()


if __name__ == "__main__":
    test_audio_service_validation()
    test_audio_service_silence_detection()
    test_whisper_service_smoke()
    test_speechbrain_emotion_smoke()
    test_api_speech_endpoints()
    print("\n==================================================")
    print("ALL SPEECH & AUDIO TESTS PASSED SUCCESSFULLY!")
    print("==================================================")
