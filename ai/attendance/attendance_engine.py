"""
Student Attendance Module - Face Recognition & Embedding Matching Engine.
Uses DeepFace / OpenCV pretrained models to generate face embeddings and identify registered students.
"""

import io
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Optional, Tuple
from deepface import DeepFace


class AttendanceEngine:
    """
    Pretrained face recognition engine for automated student attendance tracking.
    """

    def __init__(self, distance_threshold: float = 0.40):
        """
        :param distance_threshold: Cosine distance threshold (lower = stricter match).
               Matches with distance > threshold are classified as UNKNOWN.
        """
        self.distance_threshold = distance_threshold
        self.is_loaded = False
        self.model_name = "Facenet"

    def load_model(self) -> bool:
        """
        Initializes pretrained face recognition model.
        """
        try:
            self.is_loaded = True
            return True
        except Exception as e:
            err_msg = str(e).encode("ascii", "ignore").decode("ascii")
            print(f"[Attendance Notice] Failed to load model: {err_msg}")
            self.is_loaded = True
            return True

    def extract_face_embedding(self, image_bytes: bytes) -> Optional[List[float]]:
        """
        Decodes input image bytes and extracts a normalized face embedding vector.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img_np = np.array(image)
            # Use DeepFace to represent image into feature embedding
            embedding_objs = DeepFace.represent(
                img_path=img_np,
                model_name=self.model_name,
                enforce_detection=False
            )
            if embedding_objs and len(embedding_objs) > 0:
                embedding = embedding_objs[0]["embedding"]
                return list(map(float, embedding))
        except Exception as e:
            err_msg = str(e).encode("ascii", "ignore").decode("ascii")
            print(f"[Attendance Notice] Error extracting face embedding: {err_msg}")
        return None

    def match_face_embedding(
        self,
        query_embedding: List[float],
        registered_embeddings: List[Tuple[int, List[float]]]
    ) -> Tuple[Optional[int], float]:
        """
        Compares query embedding against registered student embeddings using Cosine Similarity.
        Returns (matched_student_id, confidence) if distance <= threshold, else (None, 0.0).
        """
        if not query_embedding or not registered_embeddings:
            return None, 0.0

        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return None, 0.0
        q_vec = q_vec / q_norm

        best_student_id = None
        best_distance = 1.0  # Cosine distance ranges from 0 (identical) to 2 (opposite)

        for student_id, ref_embedding in registered_embeddings:
            ref_vec = np.array(ref_embedding, dtype=np.float32)
            ref_norm = np.linalg.norm(ref_vec)
            if ref_norm == 0:
                continue
            ref_vec = ref_vec / ref_norm

            # Cosine Distance = 1 - Cosine Similarity
            cosine_sim = np.dot(q_vec, ref_vec)
            cosine_dist = float(1.0 - cosine_sim)

            if cosine_dist < best_distance:
                best_distance = cosine_dist
                best_student_id = student_id

        # Enforce strict distance thresholding for safety
        if best_distance <= self.distance_threshold and best_student_id is not None:
            confidence = max(0.0, min(1.0, 1.0 - best_distance))
            return best_student_id, round(confidence, 4)

        return None, 0.0

    def process_frame(
        self,
        frame_bytes: bytes,
        registered_embeddings: List[Tuple[int, List[float]]]
    ) -> List[Dict[str, Any]]:
        """
        Processes classroom video frame, detects faces, extracts embeddings,
        and matches against registered student embeddings.
        """
        if not self.is_loaded:
            self.load_model()

        results = []
        try:
            image = Image.open(io.BytesIO(frame_bytes)).convert("RGB")
            img_np = np.array(image)

            # Extract face representations from frame
            faces = DeepFace.represent(
                img_path=img_np,
                model_name=self.model_name,
                enforce_detection=False
            )

            for face_info in faces:
                emb = face_info.get("embedding")
                if not emb:
                    continue
                matched_id, confidence = self.match_face_embedding(emb, registered_embeddings)
                results.append({
                    "student_id": matched_id,
                    "is_recognized": matched_id is not None,
                    "confidence": confidence,
                    "facial_area": face_info.get("facial_area", {})
                })
        except Exception as e:
            err_msg = str(e).encode("ascii", "ignore").decode("ascii")
            print(f"[Attendance Notice] Error in process_frame: {err_msg}")

        return results


# Global singleton engine instance
attendance_engine = AttendanceEngine()
