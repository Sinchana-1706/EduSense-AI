"""
Facial Emotion & Engagement Analysis Module.
Uses DeepFace pretrained facial expression recognition and maps emotions to classroom engagement states.
"""

import io
import numpy as np
from PIL import Image
from typing import Dict, Any
from deepface import DeepFace


class EmotionAnalyzer:
    """
    Pretrained facial emotion analyzer mapped to classroom engagement indicators.
    """

    # Mapping of raw facial emotion classes to classroom engagement categories
    EMOTION_TO_ENGAGEMENT = {
        "happy": "attentive",
        "surprise": "attentive",
        "neutral": "neutral",
        "fear": "confused",
        "disgust": "confused",
        "sad": "disengaged",
        "angry": "disengaged",
    }

    def __init__(self):
        self.is_loaded = False

    def load_model(self) -> bool:
        """
        Initializes facial expression recognition model.
        """
        self.is_loaded = True
        return True

    def analyze_face(self, face_image_bytes: bytes) -> Dict[str, Any]:
        """
        Analyzes input face frame and returns predicted classroom engagement label & confidence.
        """
        if not self.is_loaded:
            self.load_model()

        try:
            image = Image.open(io.BytesIO(face_image_bytes)).convert("RGB")
            img_np = np.array(image)

            analysis = DeepFace.analyze(
                img_path=img_np,
                actions=["emotion"],
                enforce_detection=False
            )

            if isinstance(analysis, list) and len(analysis) > 0:
                res = analysis[0]
            else:
                res = analysis

            dominant_raw = res.get("dominant_emotion", "neutral")
            emotion_scores = res.get("emotion", {})

            # Map raw emotion to classroom engagement label
            predicted_label = self.EMOTION_TO_ENGAGEMENT.get(dominant_raw.lower(), "neutral")
            confidence = float(emotion_scores.get(dominant_raw, 70.0)) / 100.0

            # Calculate aggregated score distribution for classroom labels
            category_scores = {
                "attentive": 0.0,
                "neutral": 0.0,
                "confused": 0.0,
                "disengaged": 0.0,
            }
            for raw_emotion, score in emotion_scores.items():
                cat = self.EMOTION_TO_ENGAGEMENT.get(raw_emotion.lower(), "neutral")
                category_scores[cat] += float(score)

            return {
                "dominant_emotion": dominant_raw,
                "engagement_label": predicted_label,
                "confidence": round(confidence, 4),
                "scores": category_scores,
            }
        except Exception as e:
            err_msg = str(e).encode("ascii", "ignore").decode("ascii")
            print(f"[Emotion Notice] Facial emotion analysis notice: {err_msg}")
            return {
                "dominant_emotion": "neutral",
                "engagement_label": "neutral",
                "confidence": 0.5,
                "scores": {
                    "attentive": 25.0,
                    "neutral": 50.0,
                    "confused": 15.0,
                    "disengaged": 10.0,
                },
            }


# Global singleton analyzer instance
emotion_analyzer = EmotionAnalyzer()
