"""
Pydantic Schemas for Student & FaceEmbedding Data Validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# ----------------------------------------------------
# Student Schemas
# ----------------------------------------------------

class StudentBase(BaseModel):
    student_id: str = Field(..., example="STU-2026-001", description="Unique student identification string")
    name: str = Field(..., example="John Doe", description="Full name of the student")
    email: EmailStr = Field(..., example="john.doe@university.edu", description="Student email address")
    department: Optional[str] = Field(None, example="Computer Science", description="Academic department")
    semester: Optional[int] = Field(None, example=6, description="Current semester number")


class StudentCreate(StudentBase):
    """
    Schema for student registration input.
    Does NOT contain face embedding.
    """
    pass


class StudentResponse(StudentBase):
    """
    Schema for returning student information.
    """
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ----------------------------------------------------
# Face Embedding Schemas (Ready for future ArcFace integration)
# ----------------------------------------------------

class FaceEmbeddingCreate(BaseModel):
    student_db_id: int = Field(..., description="Database Primary Key (id) of the student")
    embedding: List[float] = Field(..., description="ArcFace feature embedding float vector")


class FaceEmbeddingResponse(BaseModel):
    id: int
    student_id: int
    embedding: List[float]
    created_at: datetime

    class Config:
        from_attributes = True
