import uuid
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class EmotionPredictionItem(BaseModel):
    student_id: Optional[str] = Field(None, description="Student profile UUID if identity is matched")
    student_name: Optional[str] = Field(None, description="Student full name if recognized")
    expression: str = Field(..., description="Predicted visible facial expression (e.g., Happiness, Neutral, Surprise)")
    confidence: float = Field(..., description="Model softmax probability score for the predicted expression (0.0 - 1.0)")
    all_scores: Optional[Dict[str, float]] = Field(None, description="Normalized softmax scores across all emotion classes")
    bbox: Optional[List[int]] = Field(None, description="Face bounding box [x1, y1, x2, y2] in pixel coordinates")


class EmotionDetectionRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded image or camera frame")
    session_id: Optional[uuid.UUID] = Field(None, description="Optional active class session UUID for association")


class EmotionDetectionResponse(BaseModel):
    success: bool = Field(..., description="True if emotion detection succeeded")
    message: str = Field(..., description="Status or feedback message")
    predictions: List[EmotionPredictionItem] = Field(default_factory=list, description="List of emotion predictions for detected faces")
    dominant_expression: Optional[str] = Field(None, description="Highest-confidence expression among detected faces")
    model_name: str = Field(..., description="Pretrained model identifier used for inference")
    disclaimer: str = Field(
        "Facial expression categories estimate visible cues only; they do not establish true emotional state, attention, or comprehension.",
        description="Ethical disclosure regarding visible expression interpretation"
    )


class AvailableModelsResponse(BaseModel):
    models: List[str] = Field(..., description="List of supported model identifiers from get_model_list()")
    current_model: str = Field(..., description="Currently active model loaded in service")
