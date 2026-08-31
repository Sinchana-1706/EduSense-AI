"""
FastAPI Router for LiveKit Real-Time Classroom Token Generation.
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.livekit import TokenRequest, TokenResponse
from app.services.livekit_service import LiveKitService

router = APIRouter(prefix="/api/v1/livekit", tags=["LiveKit Classroom"])


@router.post("/token", response_model=TokenResponse, summary="Generate LiveKit Access Token")
def generate_livekit_token(req: TokenRequest):
    """
    Generates a LiveKit JWT AccessToken for joining a WebRTC classroom.
    - **room_name**: Name of the online classroom room (e.g. 'CS-101')
    - **identity**: Unique participant identity / display name
    - **is_teacher**: Flag indicating if participant has teacher/admin capabilities
    """
    if not req.room_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room name cannot be empty."
        )
    if not req.identity.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Participant identity cannot be empty."
        )

    return LiveKitService.generate_token(
        room_name=req.room_name.strip(),
        identity=req.identity.strip(),
        is_teacher=req.is_teacher or False
    )
