"""
FastAPI Router for Student Management & Face Registration.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models.student import Student
from database.models.face_embedding import FaceEmbedding
from app.schemas.student import (
    StudentCreate,
    StudentResponse,
    FaceRegistrationResponse,
)
from ai.attendance.attendance_engine import attendance_engine

router = APIRouter(prefix="/api/v1/students", tags=["Student Management"])


@router.post("/register-face", response_model=FaceRegistrationResponse, summary="Register Student Face Embedding")
async def register_student_face(
    student_id: str = Form(..., description="Unique student ID string (e.g. STU-001)"),
    name: Optional[str] = Form(None, description="Student Name"),
    email: Optional[str] = Form(None, description="Student Email"),
    department: Optional[str] = Form("Computer Science", description="Department"),
    file: UploadFile = File(..., description="Student face image file (.jpg, .png)"),
    db: Session = Depends(get_db),
):
    """
    Registers a student's face embedding into the database.
    Accepts student_id and an image file, extracts feature embedding vector,
    and stores the embedding without retaining raw image data.
    """
    if not student_id.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student ID cannot be empty.")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded face image file is empty.")

    # Find or create student record
    student = db.query(Student).filter(Student.student_id == student_id.strip()).first()
    if not student:
        student_name = name.strip() if name and name.strip() else f"Student {student_id.strip()}"
        student_email = email.strip() if email and email.strip() else f"{student_id.strip().lower()}@university.edu"
        student = Student(
            student_id=student_id.strip(),
            name=student_name,
            email=student_email,
            department=department or "Computer Science",
            semester=6
        )
        db.add(student)
        db.commit()
        db.refresh(student)

    # Extract 128-d / 512-d feature vector embedding using AttendanceEngine
    embedding_vector = attendance_engine.extract_face_embedding(image_bytes)
    if not embedding_vector:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not detect or extract face embedding from the provided image. Ensure the face is clearly visible."
        )

    # Save embedding vector in FaceEmbedding table
    face_record = FaceEmbedding(
        student_id=student.id,
        embedding=embedding_vector,
        created_at=datetime.utcnow()
    )
    db.add(face_record)
    db.commit()

    return FaceRegistrationResponse(
        status="success",
        student_id=student.student_id,
        message=f"Face embedding successfully registered for {student.name}",
        embedding_length=len(embedding_vector),
        created_at=datetime.utcnow()
    )


@router.get("/", response_model=List[StudentResponse], summary="List Enrolled Students")
def list_students(db: Session = Depends(get_db)):
    """
    Returns list of all enrolled students and their face registration status.
    """
    students = db.query(Student).all()
    results = []
    for s in students:
        has_face = db.query(FaceEmbedding).filter(FaceEmbedding.student_id == s.id).first() is not None
        results.append(
            StudentResponse(
                id=s.id,
                student_id=s.student_id,
                name=s.name,
                email=s.email,
                department=s.department,
                semester=s.semester,
                created_at=s.created_at,
                has_face_registered=has_face
            )
        )
    return results
