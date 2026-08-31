"""
Pydantic Schemas for LiveKit Token Generation & Room Setup.
"""

from pydantic import BaseModel, Field
from typing import Optional


class TokenRequest(BaseModel):
    room_name: str = Field(..., example="CS-101", description="Classroom room name")
    identity: str = Field(..., example="Prof. Smith", description="Participant unique identity / display name")
    is_teacher: Optional[bool] = Field(False, description="Whether the participant is a teacher")


class TokenResponse(BaseModel):
    token: str = Field(..., description="JWT access token for connecting to LiveKit room")
    room_name: str = Field(..., description="Target LiveKit room name")
    identity: str = Field(..., description="Participant identity")
    livekit_url: str = Field(..., description="LiveKit WebSocket connection URL")
