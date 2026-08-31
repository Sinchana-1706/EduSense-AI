"""
Pydantic Schemas for Student Management & Face Registration.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class StudentCreate(BaseModel):
    student_id: str = Field(..., example="STU-001", description="Unique student ID string")
    name: str = Field(..., example="Alice Johnson", description="Student full name")
    email: str = Field(..., example="alice@university.edu", description="Student email address")
    department: Optional[str] = Field("Computer Science", description="Department / Major")
    semester: Optional[int] = Field(6, description="Current semester")


class StudentResponse(BaseModel):
    id: int
    student_id: str
    name: str
    email: str
    department: Optional[str] = None
    semester: Optional[int] = None
    created_at: datetime
    has_face_registered: bool = False

    class Config:
        from_attributes = True


class FaceEmbeddingCreate(BaseModel):
    student_id: int
    embedding: List[float]


class FaceEmbeddingResponse(BaseModel):
    id: int
    student_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FaceRegistrationRequest(BaseModel):
    student_id: str = Field(..., description="Target student ID string")


class FaceRegistrationResponse(BaseModel):
    status: str = "success"
    student_id: str
    message: str
    embedding_length: int
    created_at: datetime
