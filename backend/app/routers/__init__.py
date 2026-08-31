"""
Routers package initialization.
"""

from app.routers.health import router as health_router
from app.routers.students import router as students_router
from app.routers.livekit import router as livekit_router

__all__ = ["health_router", "students_router", "livekit_router"]
