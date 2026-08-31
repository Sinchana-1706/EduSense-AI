"""
FastAPI Router for Automated Student Attendance & Recognition.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models.student import Student
from database.models.face_embedding import FaceEmbedding
from database.models.attendance import AttendanceRecord
from app.schemas.attendance import (
    AttendanceRecognizeResponse,
    AttendanceRecordResponse,
    AttendanceSessionSummary,
)
from ai.attendance.attendance_engine import attendance_engine

router = APIRouter(prefix="/api/v1/attendance", tags=["Automated Attendance"])


@router.post("/recognize", response_model=AttendanceRecognizeResponse, summary="Recognize Student Face & Mark Attendance")
async def recognize_attendance(
    session_id: str = Form("CS-101", description="Classroom session ID"),
    room_name: str = Form("CS-101", description="Classroom room name"),
    file: UploadFile = File(..., description="Classroom video frame image file"),
    db: Session = Depends(get_db),
):
    """
    Processes video frame snapshot from LiveKit classroom, detects faces,
    compares embeddings against registered student database, and marks attendance.
    Enforces strict thresholding to avoid false positives on unknown faces.
    """
    frame_bytes = await file.read()
    if not frame_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded frame image is empty.")

    # Fetch all registered student embeddings from DB
    face_records = db.query(FaceEmbedding).all()
    registered_list = []
    for r in face_records:
        registered_list.append((r.student_id, r.embedding))

    # Process frame through AttendanceEngine
    recognized_faces = attendance_engine.process_frame(frame_bytes, registered_list)

    new_attendance_count = 0
    unknown_count = 0
    recognized_records: List[AttendanceRecordResponse] = []

    for match in recognized_faces:
        matched_student_db_id = match.get("student_id")
        confidence = match.get("confidence", 0.0)

        if matched_student_db_id is not None:
            student = db.query(Student).filter(Student.id == matched_student_db_id).first()
            if student:
                # Check if attendance is already recorded for this session
                existing = (
                    db.query(AttendanceRecord)
                    .filter(
                        AttendanceRecord.student_id == student.id,
                        AttendanceRecord.session_id == session_id
                    )
                    .first()
                )

                if not existing:
                    existing = AttendanceRecord(
                        student_id=student.id,
                        session_id=session_id,
                        room_name=room_name,
                        status="PRESENT",
                        confidence=confidence,
                        timestamp=datetime.utcnow()
                    )
                    db.add(existing)
                    db.commit()
                    db.refresh(existing)
                    new_attendance_count += 1

                recognized_records.append(
                    AttendanceRecordResponse(
                        id=existing.id,
                        student_id=student.id,
                        student_id_code=student.student_id,
                        student_name=student.name,
                        session_id=existing.session_id,
                        room_name=existing.room_name,
                        status=existing.status,
                        confidence=existing.confidence,
                        timestamp=existing.timestamp
                    )
                )
        else:
            unknown_count += 1

    return AttendanceRecognizeResponse(
        status="success",
        session_id=session_id,
        room_name=room_name,
        recognized_count=len(recognized_records),
        new_attendance_marked=new_attendance_count,
        unknown_count=unknown_count,
        recognized_students=recognized_records
    )


@router.get("/session/{session_id}", response_model=AttendanceSessionSummary, summary="Get Session Attendance Summary")
def get_session_attendance(session_id: str, db: Session = Depends(get_db)):
    """
    Returns attendance analytics for a specific classroom session,
    including total students, present count, absent count, and percentage.
    """
    total_enrolled = db.query(Student).count()
    if total_enrolled == 0:
        total_enrolled = 1  # Avoid division by zero

    present_records = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.session_id == session_id, AttendanceRecord.status == "PRESENT")
        .all()
    )

    present_count = len(present_records)
    absent_count = max(0, total_enrolled - present_count)
    attendance_pct = round((present_count / total_enrolled) * 100.0, 1)

    record_responses = []
    for r in present_records:
        student = db.query(Student).filter(Student.id == r.student_id).first()
        record_responses.append(
            AttendanceRecordResponse(
                id=r.id,
                student_id=r.student_id,
                student_id_code=student.student_id if student else None,
                student_name=student.name if student else "Unknown",
                session_id=r.session_id,
                room_name=r.room_name,
                status=r.status,
                confidence=r.confidence,
                timestamp=r.timestamp
            )
        )

    return AttendanceSessionSummary(
        session_id=session_id,
        total_students=total_enrolled,
        present_students=present_count,
        absent_students=absent_count,
        attendance_percentage=attendance_pct,
        records=record_responses
    )


@router.get("/student/{student_id}", response_model=List[AttendanceRecordResponse], summary="Get Student Attendance History")
def get_student_attendance(student_id: str, db: Session = Depends(get_db)):
    """
    Returns attendance record history for a given student ID code.
    """
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student {student_id} not found.")

    records = db.query(AttendanceRecord).filter(AttendanceRecord.student_id == student.id).all()
    return [
        AttendanceRecordResponse(
            id=r.id,
            student_id=r.student_id,
            student_id_code=student.student_id,
            student_name=student.name,
            session_id=r.session_id,
            room_name=r.room_name,
            status=r.status,
            confidence=r.confidence,
            timestamp=r.timestamp
        )
        for r in records
    ]
