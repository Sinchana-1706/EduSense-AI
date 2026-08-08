"""
Routers package initialization.
"""

from app.routers.health import router as health_router
from app.routers.students import router as students_router

__all__ = ["health_router", "students_router"]
