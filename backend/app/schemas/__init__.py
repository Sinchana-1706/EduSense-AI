"""
Schemas package initialization.
"""

from backend.app.schemas.student import (
    StudentCreate,
    StudentResponse,
    FaceEmbeddingCreate,
    FaceEmbeddingResponse,
)

__all__ = [
    "StudentCreate",
    "StudentResponse",
    "FaceEmbeddingCreate",
    "FaceEmbeddingResponse",
]
