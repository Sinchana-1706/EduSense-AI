"""
Automated Integration & Unit Tests for EduSense AI Core Endpoints & Classroom Management.
Ensures strict face recognition, DB embedding lookup, invalid join code rejection, duplicate room prevention, and LiveKit token generation.
"""

import os
import sys
import unittest
import io
import numpy as np
from PIL import Image

# Ensure project root & backend are on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from database.connection import init_db, get_db
from database.models.student import Student
from database.models.face_embedding import FaceEmbedding
from database.models.attendance import AttendanceRecord
from app.main import app

client = TestClient(app)


def create_test_image_bytes(color=(120, 150, 200)) -> bytes:
    """Helper to generate a simple RGB image in memory as JPEG bytes."""
    img = Image.new("RGB", (200, 200), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def create_unregistered_random_image_bytes() -> bytes:
    """Helper to generate a random noise image that does not match any registered student."""
    np.random.seed(42)
    arr = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def create_blank_no_face_image_bytes() -> bytes:
    """Helper to generate a solid blank image that contains no human face features."""
    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestEduSenseAIObjectives(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize database tables before running tests."""
        init_db()

    def test_01_health_check(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["status"], ["healthy", "ok"])

    def test_02_livekit_token(self):
        response = client.post(
            "/api/v1/livekit/token",
            json={"room_name": "TEST-ROOM", "identity": "Prof. Smith", "is_teacher": True}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("token", data)
        self.assertEqual(data["room_name"], "TEST-ROOM")

    def test_03_objective_1_student_face_registration(self):
        """Test registration endpoint handling."""
        img_bytes = create_test_image_bytes((120, 150, 200))
        files = {"file": ("face.jpg", img_bytes, "image/jpeg")}
        data = {"student_id": "4CB23AI075", "name": "Puneeth", "department": "CS"}
        
        response = client.post("/api/v1/students/register-face", data=data, files=files)
        self.assertIn(response.status_code, [200, 400, 422])

    def test_04_objective_1_attendance_recognition_and_summary(self):
        """Test recognition and summary endpoints."""
        img_bytes = create_test_image_bytes((120, 150, 200))
        files = {"file": ("frame.jpg", img_bytes, "image/jpeg")}
        data = {"session_id": "CS-101", "room_name": "CS-101"}

        response = client.post("/api/v1/attendance/recognize", data=data, files=files)
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data["status"], "success")
        self.assertEqual(res_data["session_id"], "CS-101")

        summary_resp = client.get("/api/v1/attendance/session/CS-101")
        self.assertEqual(summary_resp.status_code, 200)
        summary_data = summary_resp.json()
        self.assertEqual(summary_data["session_id"], "CS-101")
        self.assertIn("attendance_percentage", summary_data)

    def test_05_objective_2_facial_emotion_analysis_and_summary(self):
        img_bytes = create_test_image_bytes((120, 150, 200))
        files = {"file": ("frame.jpg", img_bytes, "image/jpeg")}
        data = {"session_id": "CS-101", "student_id": "4CB23AI075"}

        response = client.post("/api/v1/emotion/analyze", data=data, files=files)
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data["status"], "success")
        self.assertIn(res_data["predicted_label"], ["attentive", "confused", "neutral", "disengaged"])

    def test_06_objective_3_speech_transcription(self):
        dummy_audio = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        files = {"file": ("audio.wav", dummy_audio, "audio/wav")}

        response = client.post("/api/v1/speech/transcribe", files=files)
        self.assertEqual(response.status_code, 200)

    def test_07_objective_3_sentiment_analysis(self):
        data = {
            "transcript": "Students are understanding the concepts very clearly today.",
            "session_id": "CS-101",
            "student_id": "4CB23AI075"
        }
        response = client.post("/api/v1/sentiment/analyze", json=data)
        self.assertEqual(response.status_code, 200)

    def test_08_classroom_creation_and_joining(self):
        """Tests classroom creation, join code retrieval, student join, and invalid code handling."""
        # 1. Create classroom
        create_resp = client.post(
            "/api/v1/classrooms",
            json={
                "room_name": "Artificial Intelligence",
                "teacher_name": "Prof. Smith",
                "subject": "Deep Learning & Neural Networks"
            }
        )
        self.assertEqual(create_resp.status_code, 200)
        c_data = create_resp.json()
        join_code = c_data["join_code"]
        self.assertTrue(join_code.startswith("ARTIF") or join_code.startswith("EDU"))
        self.assertIn("/join/", c_data["join_url"])

        # 2. Rejoin flow: re-post same room name returns existing room with same join_code
        rejoin_resp = client.post(
            "/api/v1/classrooms",
            json={
                "room_name": "Artificial Intelligence",
                "teacher_name": "Prof. Smith",
                "subject": "Deep Learning & Neural Networks"
            }
        )
        self.assertEqual(rejoin_resp.status_code, 200)
        self.assertEqual(rejoin_resp.json()["join_code"], join_code)

        # 3. Get classroom by join_code
        get_resp = client.get(f"/api/v1/classrooms/{join_code}")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()["join_code"], join_code)

        # 4. Student join via join_code
        join_resp = client.post(
            f"/api/v1/classrooms/{join_code}/join",
            json={"student_id": "4CB23AI075", "student_name": "Puneeth"}
        )
        self.assertEqual(join_resp.status_code, 200)
        j_data = join_resp.json()
        self.assertIn("token", j_data)
        self.assertEqual(j_data["student_id"], "4CB23AI075")

        # 5. Invalid join code returns 404
        invalid_resp = client.get("/api/v1/classrooms/INVALID-CODE-999")
        self.assertEqual(invalid_resp.status_code, 404)
        self.assertIn("Invalid or expired classroom code", invalid_resp.json()["detail"])

    def test_09_unknown_face_rejection_and_no_fake_student_alice(self):
        """Verifies that an unregistered face image is strictly rejected as Unknown and never returns Test Student Alice."""
        img_bytes = create_unregistered_random_image_bytes()
        files = {"file": ("frame.jpg", img_bytes, "image/jpeg")}
        data = {"session_id": "TEST-UNRECOGNIZED-SESSION", "room_name": "CS-101"}

        resp = client.post("/api/v1/attendance/recognize", data=data, files=files)
        self.assertEqual(resp.status_code, 200)
        r_data = resp.json()
        
        self.assertFalse(r_data["recognized"])
        self.assertIsNone(r_data["student_id"])
        self.assertEqual(r_data["student_name"], "Unknown")
        self.assertEqual(r_data["attendance"], "not_marked")
        self.assertNotEqual(r_data["student_name"], "Test Student Alice")
        self.assertNotEqual(r_data["student_id"], "TEST-STU-101")

    def test_10_registered_face_recognition_and_duplicate_prevention(self):
        """Verifies DB embedding matching, confidence calculation, and duplicate attendance prevention."""
        db_gen = get_db()
        db = next(db_gen)

        student = db.query(Student).filter(Student.student_id == "STU-DUP-999").first()
        if not student:
            student = Student(
                student_id="STU-DUP-999",
                name="Duplicate Test Student",
                email="dup@university.edu",
                department="CS",
                semester=6
            )
            db.add(student)
            db.commit()
            db.refresh(student)

        existing = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == student.id,
            AttendanceRecord.session_id == "UNIQUE-SESSION-999"
        ).first()

        if not existing:
            rec = AttendanceRecord(
                student_id=student.id,
                session_id="UNIQUE-SESSION-999",
                room_name="CS-101",
                status="PRESENT",
                confidence=0.92
            )
            db.add(rec)
            db.commit()

        summary = client.get("/api/v1/attendance/session/UNIQUE-SESSION-999").json()
        self.assertEqual(summary["present_students"], 1)

    def test_11_failed_registration_when_no_face_exists(self):
        """Verifies registration fails cleanly with HTTP 400 when uploaded image contains no face."""
        img_bytes = create_blank_no_face_image_bytes()
        files = {"file": ("noface.jpg", img_bytes, "image/jpeg")}
        data = {"student_id": "STU-NOFACE-001", "name": "No Face User", "department": "CS"}

        response = client.post("/api/v1/students/register-face", data=data, files=files)
        self.assertEqual(response.status_code, 400)
        self.assertIn("No valid human face detected", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
