"""
FastAPI Router for Health Check Endpoints.
"""

from fastapi import APIRouter
from app.services.health_service import HealthService

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Basic Health Check")
def health_check():
    """
    GET /health
    Returns system status JSON.
    """
    return HealthService.get_system_health()
