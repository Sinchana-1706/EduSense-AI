"""
Automated Integration & Unit Tests for EduSense AI Objectives 1, 2, and 3 Endpoints.
"""

import os
import sys
import unittest
import io
from PIL import Image

# Ensure project root & backend are on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from database.connection import init_db
from app.main import app

client = TestClient(app)


def create_test_image_bytes() -> bytes:
    """Helper to generate a simple RGB image in memory as JPEG bytes."""
    img = Image.new("RGB", (200, 200), color=(120, 150, 200))
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
        img_bytes = create_test_image_bytes()
        files = {"file": ("face.jpg", img_bytes, "image/jpeg")}
        data = {"student_id": "TEST-STU-101", "name": "Test Student Alice", "department": "CS"}
        
        response = client.post("/api/v1/students/register-face", data=data, files=files)
        self.assertIn(response.status_code, [200, 422])
        if response.status_code == 200:
            res_data = response.json()
            self.assertEqual(res_data["status"], "success")
            self.assertEqual(res_data["student_id"], "TEST-STU-101")

    def test_04_objective_1_attendance_recognition_and_summary(self):
        img_bytes = create_test_image_bytes()
        files = {"file": ("frame.jpg", img_bytes, "image/jpeg")}
        data = {"session_id": "CS-101", "room_name": "CS-101"}

        response = client.post("/api/v1/attendance/recognize", data=data, files=files)
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data["status"], "success")
        self.assertEqual(res_data["session_id"], "CS-101")

        # Query summary endpoint
        summary_resp = client.get("/api/v1/attendance/session/CS-101")
        self.assertEqual(summary_resp.status_code, 200)
        summary_data = summary_resp.json()
        self.assertEqual(summary_data["session_id"], "CS-101")
        self.assertIn("attendance_percentage", summary_data)

    def test_05_objective_2_facial_emotion_analysis_and_summary(self):
        img_bytes = create_test_image_bytes()
        files = {"file": ("frame.jpg", img_bytes, "image/jpeg")}
        data = {"session_id": "CS-101", "student_id": "TEST-STU-101"}

        response = client.post("/api/v1/emotion/analyze", data=data, files=files)
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data["status"], "success")
        self.assertIn(res_data["predicted_label"], ["attentive", "confused", "neutral", "disengaged"])

        # Query summary endpoint
        summary_resp = client.get("/api/v1/emotion/session/CS-101")
        self.assertEqual(summary_resp.status_code, 200)
        summary_data = summary_resp.json()
        self.assertEqual(summary_data["session_id"], "CS-101")
        self.assertIn("distribution", summary_data)
        self.assertIn("attentive", summary_data["distribution"])

    def test_06_objective_3_speech_transcription(self):
        # Create dummy WAV audio bytes
        dummy_audio = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        files = {"file": ("audio.wav", dummy_audio, "audio/wav")}

        response = client.post("/api/v1/speech/transcribe", files=files)
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data["status"], "success")
        self.assertIn("transcript", res_data)

    def test_07_objective_3_sentiment_analysis_and_summary(self):
        data = {
            "transcript": "Students are understanding the concepts very clearly today and asking great questions.",
            "session_id": "CS-101",
            "student_id": "TEST-STU-101"
        }

        response = client.post("/api/v1/sentiment/analyze", json=data)
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data["status"], "success")
        self.assertEqual(res_data["sentiment"], "positive")

        # Query summary endpoint
        summary_resp = client.get("/api/v1/sentiment/session/CS-101")
        self.assertEqual(summary_resp.status_code, 200)
        summary_data = summary_resp.json()
        self.assertEqual(summary_data["session_id"], "CS-101")
        self.assertIn("distribution", summary_data)
        self.assertIn("positive", summary_data["distribution"])


if __name__ == "__main__":
    unittest.main()
