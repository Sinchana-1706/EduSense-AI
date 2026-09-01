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
    recognized: bool = False
    student_id: Optional[str] = None
    student_name: Optional[str] = "Unknown"
    confidence: float = 0.0
    attendance: str = "not_marked"
    session_id: str
    room_name: str
    timestamp: str
    recognized_count: int = 0
    new_attendance_marked: int = 0
    unknown_count: int = 0
    recognized_students: List[AttendanceRecordResponse] = []


class AttendanceSessionSummary(BaseModel):
    session_id: str
    total_students: int
    present_students: int
    absent_students: int
    attendance_percentage: float
    records: List[AttendanceRecordResponse]
