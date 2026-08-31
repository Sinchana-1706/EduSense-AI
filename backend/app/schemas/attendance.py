"""
Pydantic Schemas for Automated Student Attendance.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AttendanceRecordResponse(BaseModel):
    id: int
    student_id: int
    student_id_code: Optional[str] = None
    student_name: Optional[str] = None
    session_id: str
    room_name: str
    status: str
    confidence: float
    timestamp: datetime

    class Config:
        from_attributes = True


class AttendanceRecognizeResponse(BaseModel):
    status: str = "success"
    session_id: str
    room_name: str
    recognized_count: int
    new_attendance_marked: int
    unknown_count: int
    recognized_students: List[AttendanceRecordResponse]


class AttendanceSessionSummary(BaseModel):
    session_id: str
    total_students: int
    present_students: int
    absent_students: int
    attendance_percentage: float
    records: List[AttendanceRecordResponse]
