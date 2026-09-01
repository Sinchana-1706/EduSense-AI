"""
Pydantic Schemas for Classroom Management & Joining.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ClassroomCreate(BaseModel):
    room_name: str = Field(..., description="Classroom name (e.g. CS-101)", example="CS-101")
    teacher_name: str = Field(..., description="Teacher name (e.g. Prof. Smith)", example="Prof. Smith")
    subject: Optional[str] = Field(None, description="Optional subject name", example="Artificial Intelligence")
    class_section: Optional[str] = Field(None, description="Optional class or section", example="Section A")


class ClassroomResponse(BaseModel):
    classroom_id: int
    room_name: str
    subject: Optional[str] = None
    teacher_name: str
    join_code: str
    join_url: str
    livekit_room_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class StudentJoinRequest(BaseModel):
    student_id: str = Field(..., description="Student unique ID (e.g. 4CB23AI075)", example="4CB23AI075")
    student_name: str = Field(..., description="Student full name", example="Puneeth")
    join_code: Optional[str] = Field(None, description="Classroom join code (e.g. EDU-A7K92)", example="EDU-A7K92")


class StudentJoinResponse(BaseModel):
    classroom: ClassroomResponse
    token: str
    livekit_url: str
    student_id: str
    student_name: str
