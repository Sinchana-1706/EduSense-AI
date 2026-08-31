"""
LiveKit Token Service for EduSense AI.
Generates JWT access tokens for LiveKit real-time WebRTC classroom sessions.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any
from app.config.settings import settings

# Attempt importing official livekit-api, fallback to PyJWT if needed
try:
    from livekit.api import AccessToken, VideoGrants
    HAS_LIVEKIT_SDK = True
except ImportError:
    HAS_LIVEKIT_SDK = False
    import jwt


class LiveKitService:

    @staticmethod
    def generate_token(room_name: str, identity: str, is_teacher: bool = False) -> Dict[str, Any]:
        """
        Generates a LiveKit JWT AccessToken for joining a WebRTC classroom room.
        """
        api_key = settings.LIVEKIT_API_KEY
        api_secret = settings.LIVEKIT_API_SECRET
        livekit_url = settings.LIVEKIT_URL

        if HAS_LIVEKIT_SDK:
            # Use official LiveKit Python SDK
            grants = VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
                room_admin=is_teacher,
            )
            token_builder = AccessToken(
                api_key=api_key,
                api_secret=api_secret,
            )
            token_builder.with_identity(identity)
            token_builder.with_name(identity)
            token_builder.with_grants(grants)
            token_builder.with_ttl(timedelta(hours=24))
            token_str = token_builder.to_jwt()
        else:
            # Fallback to PyJWT standard token creation matching LiveKit JWT spec
            now = int(time.time())
            payload = {
                "iss": api_key,
                "sub": identity,
                "name": identity,
                "nbf": now - 5,
                "exp": now + 86400,  # Valid for 24 hours
                "video": {
                    "roomJoin": True,
                    "room": room_name,
                    "canPublish": True,
                    "canSubscribe": True,
                    "canPublishData": True,
                    "roomAdmin": is_teacher,
                }
            }
            token_str = jwt.encode(payload, api_secret, algorithm="HS256")

        return {
            "token": token_str,
            "room_name": room_name,
            "identity": identity,
            "livekit_url": livekit_url,
        }
