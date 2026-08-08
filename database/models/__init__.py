"""
Database models package initialization.
"""

from database.models.student import Student
from database.models.face_embedding import FaceEmbedding

__all__ = ["Student", "FaceEmbedding"]
