import os
import sys
import uuid
import base64
import cv2
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from fastapi.testclient import TestClient

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.models.enums import UserRole, SessionStatus, AttendanceStatus
from app.models.classroom import Classroom
from app.models.session import ClassSession, SessionParticipant
from app.models.profile import StudentProfile, TeacherProfile
from app.models.stubs import FaceEmbedding, AttendanceRecord, FacialAnalysis
from app.core.security import create_access_token
from app.services.face_service import FaceService
from app.services.emotion_service import EmotionService


def generate_face_image_base64() -> str:
    """Generates a synthetic face frame with oval face and eye/mouth features."""
    img = np.full((480, 640, 3), 200, dtype=np.uint8)
    cv2.ellipse(img, (320, 240), (100, 140), 0, 0, 360, (180, 150, 130), -1)
    cv2.circle(img, (280, 200), 15, (50, 50, 50), -1)
    cv2.circle(img, (360, 200), 15, (50, 50, 50), -1)
    cv2.ellipse(img, (320, 270), (45, 15), 0, 0, 180, (50, 50, 50), 3)
    _, buffer = cv2.imencode('.jpg', img)
    return base64.b64encode(buffer).decode('utf-8')


def get_real_sample_image() -> Optional[np.ndarray]:
    """Finds a real test face image from insightface package assets if available."""
    t1_path = os.path.join(os.path.dirname(__file__), "venv", "Lib", "site-packages", "insightface", "data", "images", "t1.jpg")
    if os.path.isfile(t1_path):
        return cv2.imread(t1_path)
    return None


def get_real_single_face_frame() -> Optional[np.ndarray]:
    """Generates a realistic single-face webcam frame from t1.jpg face crop for attendance."""
    real_img = get_real_sample_image()
    if real_img is None:
        return None
    face_svc = FaceService.get_instance()
    faces = face_svc.detect_faces(real_img)
    if not faces:
        return None
    bbox = faces[0].bbox.astype(int)
    crop = face_svc.extract_face_crop(real_img, bbox, pad_ratio=0.3)
    frame = np.full((480, 640, 3), 220, dtype=np.uint8)
    crop_resized = cv2.resize(crop, (200, 200))
    frame[140:340, 220:420] = crop_resized
    return frame



def test_1_service_initialization():
    print("\n--- TEST 1: EmotionService Initialization ---")
    svc = EmotionService.get_instance()
    assert svc is not None, "EmotionService singleton should not be None"
    assert svc.is_loaded, "EmotionService model should be loaded successfully"
    info = svc.get_model_info()
    print(f"Loaded model: {info['model_name']} ({info['engine']}) on {info['device']}")
    print(f"Supported classes ({len(info['supported_classes'])}): {info['supported_classes']}")
    assert "Happiness" in info["supported_classes"], "Happiness must be a supported class"
    assert "Neutral" in info["supported_classes"], "Neutral must be a supported class"
    print("PASS: EmotionService initialization verified.")


def test_2_predict_emotion_from_crop():
    print("\n--- TEST 2: Emotion Prediction on Face Crop ---")
    svc = EmotionService.get_instance()
    
    # 224x224 synthetic crop
    crop = np.full((224, 224, 3), 150, dtype=np.uint8)
    cv2.circle(crop, (70, 80), 15, (40, 40, 40), -1)
    cv2.circle(crop, (154, 80), 15, (40, 40, 40), -1)
    cv2.ellipse(crop, (112, 140), (40, 20), 0, 0, 180, (40, 40, 40), 3)

    result = svc.predict_emotion_from_crop(crop)
    assert result is not None, "Prediction should not be None for valid crop"
    assert "expression" in result, "Result must contain expression"
    assert "confidence" in result, "Result must contain confidence score"
    assert 0.0 <= result["confidence"] <= 1.0, f"Confidence {result['confidence']} must be between 0.0 and 1.0"
    assert "all_scores" in result, "Result must contain all_scores distribution"
    
    # Verify probabilities sum to ~1.0
    prob_sum = sum(result["all_scores"].values())
    assert 0.98 <= prob_sum <= 1.02, f"Probabilities sum ({prob_sum}) should approximate 1.0"
    print(f"PASS: Predicted '{result['expression']}' with confidence {result['confidence']:.4f}")


def test_3_edge_cases_no_face_empty_crop():
    print("\n--- TEST 3: Edge Cases (Empty, Blank, Invalid Inputs) ---")
    svc = EmotionService.get_instance()

    # Empty crop
    empty_crop = np.zeros((0, 0, 3), dtype=np.uint8)
    assert svc.predict_emotion_from_crop(empty_crop) is None, "Empty crop should return None"

    # None crop
    assert svc.predict_emotion_from_crop(None) is None, "None crop should return None"

    # Blank image with no faces
    blank_img = np.zeros((480, 640, 3), dtype=np.uint8)
    preds = svc.process_image_emotions(blank_img)
    assert len(preds) == 0, "Blank frame should detect zero emotions"
    print("PASS: Edge cases handled safely without crashes.")


def test_4_real_face_inference():
    print("\n--- TEST 4: Real Face Image Inference ---")
    real_img = get_real_sample_image()
    if real_img is None:
        print("SKIP: Real face asset not found, skipping real face test.")
        return

    svc = EmotionService.get_instance()
    face_svc = FaceService.get_instance()

    faces = face_svc.detect_faces(real_img)
    print(f"InsightFace detected {len(faces)} face(s) in real test image.")
    assert len(faces) >= 1, "Should detect at least 1 face in real test image"

    predictions = svc.process_image_emotions(real_img, faces=faces)
    assert len(predictions) >= 1, "Should produce emotion prediction for detected face"
    top_pred = predictions[0]
    print(f"PASS: Real face detected as '{top_pred['expression']}' (conf: {top_pred['confidence']:.4f}, bbox: {top_pred.get('bbox')})")


def test_5_api_emotion_endpoints():
    print("\n--- TEST 5: API Endpoints (POST /api/face/emotion and GET /api/face/emotion/models) ---")
    client = TestClient(app)
    db = SessionLocal()

    try:
        # Create student user
        email = f"emotion_test_{uuid.uuid4().hex[:6]}@edusense.ai"
        user = User(
            email=email,
            password_hash="hashed_pw",
            full_name="Emotion Test Student",
            role=UserRole.STUDENT,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        profile = StudentProfile(
            user_id=user.id,
            student_id_number=f"EMO_{uuid.uuid4().hex[:6]}",
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

        token = create_access_token({"sub": str(user.id), "role": user.role.value})
        headers = {"Authorization": f"Bearer {token}"}

        # 1. GET /api/face/emotion/models
        resp_models = client.get("/api/face/emotion/models", headers=headers)
        assert resp_models.status_code == 200, f"Expected 200, got {resp_models.status_code}"
        models_data = resp_models.json()
        assert "models" in models_data, "Response must include models list"
        assert "current_model" in models_data, "Response must include current_model"
        print(f"Available models API: {models_data['models']}, active: {models_data['current_model']}")

        # 2. POST /api/face/emotion with blank frame (no face)
        blank_b64 = base64.b64encode(cv2.imencode('.jpg', np.zeros((480, 640, 3), dtype=np.uint8))[1]).decode('utf-8')
        resp_blank = client.post("/api/face/emotion", json={"image_base64": blank_b64}, headers=headers)
        assert resp_blank.status_code == 200
        blank_data = resp_blank.json()
        assert blank_data["success"] is False, "Expected success=False on no faces"
        assert len(blank_data["predictions"]) == 0

        # 3. POST /api/face/emotion with real test face image
        real_img = get_real_single_face_frame()
        if real_img is not None:
            _, buf = cv2.imencode('.jpg', real_img)
            real_b64 = base64.b64encode(buf).decode('utf-8')
            resp_real = client.post("/api/face/emotion", json={"image_base64": real_b64}, headers=headers)
            assert resp_real.status_code == 200
            data_real = resp_real.json()
            assert data_real["success"] is True, f"Failed: {data_real.get('message')}"
            assert len(data_real["predictions"]) >= 1, "Should have at least 1 prediction"
            pred0 = data_real["predictions"][0]
            assert pred0["student_id"] == str(profile.id), "Should associate authenticated student_id"
            assert pred0["student_name"] == user.full_name, "Should associate student_name"
            assert "expression" in pred0
            assert "confidence" in pred0
            assert "disclaimer" in data_real
            print(f"PASS: POST /api/face/emotion returned: {pred0['expression']} (conf: {pred0['confidence']:.2f})")

    finally:
        db.close()


def test_6_attendance_verification_with_emotion_integration():
    print("\n--- TEST 6: Attendance Verification with Integrated Facial Emotion Logging ---")
    client = TestClient(app)
    db = SessionLocal()

    try:
        # Create teacher and classroom
        teacher_user = User(
            email=f"teacher_{uuid.uuid4().hex[:6]}@edusense.ai",
            password_hash="pw",
            full_name="Prof. Attendance",
            role=UserRole.TEACHER,
            is_active=True,
        )
        db.add(teacher_user)
        db.commit()
        db.refresh(teacher_user)

        teacher_prof = TeacherProfile(user_id=teacher_user.id, employee_id=f"EMP_{uuid.uuid4().hex[:4]}")
        db.add(teacher_prof)
        db.commit()

        classroom = Classroom(
            title="AI Emotion Classroom",
            course_code=f"EMO_{uuid.uuid4().hex[:4].upper()}",
            teacher_id=teacher_prof.id,
            livekit_room_name=f"room_emo_{uuid.uuid4().hex[:6]}",
            is_active=True,
        )
        db.add(classroom)
        db.commit()

        session_obj = ClassSession(
            classroom_id=classroom.id,
            title="Live Session Emotion Test",
            status=SessionStatus.ACTIVE,
            scheduled_start_time=datetime.now(timezone.utc),
            scheduled_end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            actual_start_time=datetime.now(timezone.utc),
        )
        db.add(session_obj)
        db.commit()

        # Create student and participant
        student_user = User(
            email=f"stud_{uuid.uuid4().hex[:6]}@edusense.ai",
            password_hash="pw",
            full_name="Verified Student Emo",
            role=UserRole.STUDENT,
            is_active=True,
        )
        db.add(student_user)
        db.commit()

        student_prof = StudentProfile(user_id=student_user.id, student_id_number=f"STU_{uuid.uuid4().hex[:6]}")
        db.add(student_prof)
        db.commit()

        participant = SessionParticipant(
            session_id=session_obj.id,
            user_id=student_user.id,
            role=UserRole.STUDENT,
            joined_at=datetime.now(timezone.utc),
        )
        db.add(participant)
        db.commit()

        # Enroll face for student using real sample image if available
        real_img = get_real_single_face_frame()
        if real_img is None:
            print("SKIP: Real face image required for ArcFace matching.")
            return

        face_svc = FaceService.get_instance()
        detected_faces = face_svc.detect_faces(real_img)
        assert len(detected_faces) >= 1
        embedding = face_svc.generate_embedding(detected_faces[0])

        face_record = FaceEmbedding(
            student_id=student_prof.id,
            embedding_dim=512,
            embedding_data={
                "mean_embedding": embedding,
                "sample_embeddings": [embedding],
                "enrolled_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        db.add(face_record)
        db.commit()

        # Call POST /api/attendance/verify
        token = create_access_token({"sub": str(student_user.id), "role": student_user.role.value})
        headers = {"Authorization": f"Bearer {token}"}

        _, buf = cv2.imencode('.jpg', real_img)
        frame_b64 = base64.b64encode(buf).decode('utf-8')

        resp = client.post(
            "/api/attendance/verify",
            json={"session_id": str(session_obj.id), "image_base64": frame_b64},
            headers=headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        print(f"Attendance response reason: {data['reason']}")
        assert data["reason"] in ("CONFIRMED", "PENDING_TEMPORAL"), f"Unexpected reason: {data['reason']}"

        # Verify facial_emotion is present in response
        assert "facial_emotion" in data, "Response must include facial_emotion"
        emo_data = data["facial_emotion"]
        assert emo_data is not None, "facial_emotion should not be None on successful match"
        assert emo_data["expression"] is not None
        assert emo_data["confidence"] > 0.0
        print(f"PASS: Attendance returned facial emotion: '{emo_data['expression']}' (conf: {emo_data['confidence']:.2f})")

        # Verify FacialAnalysis table has recorded the observation
        fa_record = db.query(FacialAnalysis).filter(
            FacialAnalysis.session_id == session_obj.id,
            FacialAnalysis.student_id == student_prof.id,
        ).first()
        assert fa_record is not None, "FacialAnalysis database record should be saved"
        assert fa_record.dominant_emotion == emo_data["expression"]
        print(f"PASS: FacialAnalysis record saved in DB with dominant_emotion='{fa_record.dominant_emotion}'")

    finally:
        db.close()


if __name__ == "__main__":
    test_1_service_initialization()
    test_2_predict_emotion_from_crop()
    test_3_edge_cases_no_face_empty_crop()
    test_4_real_face_inference()
    test_5_api_emotion_endpoints()
    test_6_attendance_verification_with_emotion_integration()
    print("\n==================================================")
    print("ALL EMOTION SERVICE TESTS PASSED SUCCESSFULLY!")
    print("==================================================")
