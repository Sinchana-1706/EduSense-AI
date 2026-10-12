import logging
import numpy as np
import cv2
from typing import List, Dict, Any, Optional, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)

EMOTIEFFLIB_AVAILABLE = False
try:
    from emotiefflib.facial_analysis import EmotiEffLibRecognizer, get_model_list
    EMOTIEFFLIB_AVAILABLE = True
except ImportError:
    EmotiEffLibRecognizer = None
    get_model_list = None
    logger.warning("EmotiEffLib package not found in Python environment. Operating in stub mode.")


class EmotionService:
    _instance: Optional["EmotionService"] = None

    def __init__(self):
        self.model_name = settings.EMOTION_MODEL_NAME
        self.engine = settings.EMOTION_INFERENCE_ENGINE
        self.device = settings.EMOTION_DEVICE
        self.recognizer = None
        self.is_loaded = False
        self.idx_to_class = {}

        logger.info(f"Initializing EmotionService (model: '{self.model_name}', engine: '{self.engine}', device: '{self.device}')...")

        if not EMOTIEFFLIB_AVAILABLE:
            logger.warning("EmotiEffLib is not available. Emotion detection service disabled.")
            return

        try:
            available_models = get_model_list()
            if self.model_name not in available_models:
                logger.warning(
                    f"Configured model '{self.model_name}' not in get_model_list() ({available_models}). Falling back to '{available_models[0]}'."
                )
                self.model_name = available_models[0]

            self.recognizer = EmotiEffLibRecognizer(
                engine=self.engine,
                model_name=self.model_name,
                device=self.device,
            )
            self.idx_to_class = getattr(self.recognizer, "idx_to_emotion_class", {})
            self.is_loaded = True
            logger.info(f"EmotionService loaded successfully with model '{self.model_name}'. Classes: {list(self.idx_to_class.values())}")
        except Exception as e:
            logger.error(f"Failed to load EmotiEffLib model '{self.model_name}': {e}", exc_info=True)
            self.recognizer = None
            self.is_loaded = False

    @classmethod
    def get_instance(cls) -> "EmotionService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_available_models(self) -> List[str]:
        if EMOTIEFFLIB_AVAILABLE and get_model_list:
            return get_model_list()
        return ["enet_b0_8_best_vgaf"]

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "engine": self.engine,
            "device": self.device,
            "is_loaded": self.is_loaded,
            "supported_classes": list(self.idx_to_class.values()) if self.idx_to_class else [],
        }

    def predict_emotion_from_crop(self, face_crop: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Runs EmotiEffLib facial expression inference on a single BGR face crop.
        - Converts BGR to RGB
        - Computes normalized softmax probabilities (logits=False)
        - Returns dominant expression, confidence score, and distribution dictionary
        """
        if not self.is_loaded or self.recognizer is None:
            logger.warning("EmotionService model not loaded. Skipping prediction.")
            return None

        if face_crop is None or face_crop.size == 0:
            return None

        try:
            # EmotiEffLib expects RGB format with ImageNet normalization
            rgb_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
            emotions, scores = self.recognizer.predict_emotions(rgb_crop, logits=False)

            if not emotions or scores is None or len(scores) == 0:
                return None

            dominant_expression = str(emotions[0])
            prob_vector = scores[0]

            confidence = float(np.max(prob_vector))

            all_scores: Dict[str, float] = {}
            if self.idx_to_class:
                for idx, class_name in self.idx_to_class.items():
                    if idx < len(prob_vector):
                        all_scores[class_name] = float(round(float(prob_vector[idx]), 4))

            return {
                "expression": dominant_expression,
                "confidence": float(round(confidence, 4)),
                "all_scores": all_scores,
            }
        except Exception as e:
            logger.error(f"Error predicting emotion from face crop: {e}", exc_info=True)
            return None

    def process_image_emotions(
        self, image: np.ndarray, faces: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Processes a full BGR image for facial expression recognition:
        1. Uses detected faces or calls FaceService detector if faces not provided.
        2. Extracts valid cropped regions.
        3. Runs emotion prediction on each face crop.
        4. Returns list of predictions with bounding boxes.
        """
        if image is None or image.size == 0:
            return []

        h, w = image.shape[:2]

        if faces is None:
            from app.services.face_service import FaceService
            face_service = FaceService.get_instance()
            faces = face_service.detect_faces(image)

        if not faces:
            return []

        predictions: List[Dict[str, Any]] = []

        for face in faces:
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = [int(v) for v in bbox]

            face_w = int(x2 - x1)
            face_h = int(y2 - y1)

            # Safety bounds check
            if face_w < 20 or face_h < 20:
                continue

            # Safe crop with padding
            pad_x = int(face_w * 0.1)
            pad_y = int(face_h * 0.1)
            crop_x1 = max(0, x1 - pad_x)
            crop_y1 = max(0, y1 - pad_y)
            crop_x2 = min(w, x2 + pad_x)
            crop_y2 = min(h, y2 + pad_y)

            face_crop = image[crop_y1:crop_y2, crop_x1:crop_x2]
            if face_crop.size == 0:
                continue

            pred = self.predict_emotion_from_crop(face_crop)
            if pred:
                pred["bbox"] = [x1, y1, x2, y2]
                predictions.append(pred)

        return predictions
