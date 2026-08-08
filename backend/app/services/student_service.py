"""
Student Service Business Logic for Database CRUD Operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from database.models.student import Student
from app.schemas.student import StudentCreate


class StudentService:

    @staticmethod
    def create_student(db: Session, student_in: StudentCreate) -> Student:
        """
        Creates a new student record in PostgreSQL database.
        Raises HTTP 400 if student_id or email already exists.
        """
        # Check if student_id already exists
        existing_student = db.query(Student).filter(Student.student_id == student_in.student_id).first()
        if existing_student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Student with student_id '{student_in.student_id}' already exists."
            )

        # Check if email already exists
        existing_email = db.query(Student).filter(Student.email == student_in.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Student with email '{student_in.email}' already exists."
            )

        new_student = Student(
            student_id=student_in.student_id,
            name=student_in.name,
            email=student_in.email,
            department=student_in.department,
            semester=student_in.semester
        )

        try:
            db.add(new_student)
            db.commit()
            db.refresh(new_student)
            return new_student
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity constraint violation."
            )

    @staticmethod
    def get_all_students(db: Session, skip: int = 0, limit: int = 100) -> List[Student]:
        """
        Retrieves a list of all registered students with pagination.
        """
        return db.query(Student).offset(skip).limit(limit).all()

    @staticmethod
    def get_student_by_student_id(db: Session, student_id: str) -> Student:
        """
        Retrieves a single student record by student_id string.
        Raises HTTP 404 if not found.
        """
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with student_id '{student_id}' not found."
            )
        return student
