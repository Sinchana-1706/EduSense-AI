"""
FastAPI Router for Student Management API Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from database.connection import get_db
from app.schemas.student import StudentCreate, StudentResponse
from app.services.student_service import StudentService

router = APIRouter(prefix="/api/v1/students", tags=["Students"])


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED, summary="Add a new Student")
def create_student(student_in: StudentCreate, db: Session = Depends(get_db)):
    """
    Registers a new student record into the PostgreSQL database.
    """
    return StudentService.create_student(db=db, student_in=student_in)


@router.get("", response_model=List[StudentResponse], summary="Get all Students")
def get_all_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieves all registered student records.
    """
    return StudentService.get_all_students(db=db, skip=skip, limit=limit)


@router.get("/{student_id}", response_model=StudentResponse, summary="Get Student by student_id")
def get_student_by_id(student_id: str, db: Session = Depends(get_db)):
    """
    Retrieves student details for a given unique student_id.
    """
    return StudentService.get_student_by_student_id(db=db, student_id=student_id)
