"""
Health Service business logic.
"""

from datetime import datetime
from typing import Dict, Any
from app.config.settings import settings


class HealthService:
    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """
        Gathers system health details for GET /health response.
        """
        return {
            "status": "ok",
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "services": {
                "api": "healthy",
                "database": "configured (PostgreSQL)",
                "ai_engine": "initialized (placeholders)"
            }
        }
