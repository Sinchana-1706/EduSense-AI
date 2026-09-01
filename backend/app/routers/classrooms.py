"""
FastAPI Router for Classroom Management & Student/Teacher Joining.
Supports Classroom Creation, Code Validation, Direct Join Links, and Rejoining without duplication.
"""

import re
import random
import string
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models.classroom import Classroom
from database.models.student import Student
from app.schemas.classroom import (
    ClassroomCreate,
    ClassroomResponse,
    StudentJoinRequest,
    StudentJoinResponse,
)
from app.services.livekit_service import LiveKitService

router = APIRouter(prefix="/api/v1/classrooms", tags=["Classroom Management"])


def generate_unique_join_code(room_name: str, db: Session) -> str:
    """
    Generates a unique short join code like 'EDU-A7K92' or 'CS101-A7K92'.
    """
    clean_prefix = re.sub(r"[^A-Za-z0-9]", "", room_name).upper()[:5]
    if not clean_prefix or clean_prefix in ["ROOM", "CLASS"]:
        clean_prefix = "EDU"

    for _ in range(50):
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        code = f"{clean_prefix}-{suffix}"
        existing = db.query(Classroom).filter(Classroom.join_code == code).first()
        if not existing:
            return code

    return f"EDU-{''.join(random.choices(string.ascii_uppercase + string.digits, k=5))}"


@router.post("", response_model=ClassroomResponse, summary="Create or Rejoin Online Classroom")
@router.post("/", response_model=ClassroomResponse, summary="Create or Rejoin Online Classroom (trailing slash)")
def create_classroom(req: ClassroomCreate, db: Session = Depends(get_db)):
    """
    Creates a new online classroom or returns an existing active classroom for the given room name/subject.
    Prevents duplicate classroom creation when teacher enters or rejoins an existing room name or code.
    """
    room_name = req.room_name.strip()
    teacher_name = req.teacher_name.strip()

    if not room_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Room name cannot be empty.")
    if not teacher_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Teacher name cannot be empty.")

    # Check if a classroom with matching join_code or room_name already exists
    existing = db.query(Classroom).filter(
        Classroom.is_active == True,
        (Classroom.join_code == room_name.upper()) | (Classroom.room_name.ilike(room_name))
    ).first()

    if existing:
        join_url = f"http://localhost:5173/join/{existing.join_code}"
        return ClassroomResponse(
            classroom_id=existing.id,
            room_name=existing.room_name,
            subject=existing.subject,
            teacher_name=existing.teacher_name,
            join_code=existing.join_code,
            join_url=join_url,
            livekit_room_name=existing.livekit_room_name,
            is_active=existing.is_active,
            created_at=existing.created_at,
        )

    join_code = generate_unique_join_code(room_name, db)
    livekit_room = f"livekit-{room_name.lower()}-{join_code.lower()}"

    classroom = Classroom(
        room_name=room_name,
        subject=req.subject.strip() if req.subject else None,
        teacher_name=teacher_name,
        join_code=join_code,
        livekit_room_name=livekit_room,
        is_active=True,
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)

    join_url = f"http://localhost:5173/join/{join_code}"

    return ClassroomResponse(
        classroom_id=classroom.id,
        room_name=classroom.room_name,
        subject=classroom.subject,
        teacher_name=classroom.teacher_name,
        join_code=classroom.join_code,
        join_url=join_url,
        livekit_room_name=classroom.livekit_room_name,
        is_active=classroom.is_active,
        created_at=classroom.created_at,
    )


@router.get("/{join_code}", response_model=ClassroomResponse, summary="Get Classroom Details by Join Code")
def get_classroom_by_code(join_code: str, db: Session = Depends(get_db)):
    """
    Returns public metadata for an active classroom by join code.
    Raises HTTP 404 with detail 'Invalid or expired classroom code.' if code is not found or inactive.
    """
    code_clean = join_code.strip().upper()
    classroom = db.query(Classroom).filter(Classroom.join_code == code_clean).first()

    if not classroom or not classroom.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired classroom code."
        )

    join_url = f"http://localhost:5173/join/{classroom.join_code}"

    return ClassroomResponse(
        classroom_id=classroom.id,
        room_name=classroom.room_name,
        subject=classroom.subject,
        teacher_name=classroom.teacher_name,
        join_code=classroom.join_code,
        join_url=join_url,
        livekit_room_name=classroom.livekit_room_name,
        is_active=classroom.is_active,
        created_at=classroom.created_at,
    )


@router.post("/join", response_model=StudentJoinResponse, summary="Join Classroom as Student (Body Request)")
def join_classroom_body(
    req: StudentJoinRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint accepting join_code within the JSON body.
    """
    code = req.join_code
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Join code is required.")
    return join_classroom(join_code=code, req=req, db=db)


@router.post("/{join_code}/join", response_model=StudentJoinResponse, summary="Join Classroom as Student (Path Parameter)")
def join_classroom(
    join_code: str,
    req: StudentJoinRequest,
    db: Session = Depends(get_db)
):
    """
    Validates a student join request and generates a LiveKit JWT token for the classroom session.
    """
    code_clean = join_code.strip().upper()
    classroom = db.query(Classroom).filter(Classroom.join_code == code_clean).first()

    if not classroom or not classroom.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired classroom code."
        )

    student_id = req.student_id.strip()
    student_name = req.student_name.strip()

    if not student_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student ID cannot be empty.")
    if not student_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student name cannot be empty.")

    # Find or register student record
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        student = Student(
            student_id=student_id,
            name=student_name,
            email=f"{student_id.lower()}@university.edu",
            department="Computer Science",
            semester=6
        )
        db.add(student)
        db.commit()
        db.refresh(student)

    # Generate LiveKit access token for student
    token_response = LiveKitService.generate_token(
        room_name=classroom.livekit_room_name,
        identity=student_name,
        is_teacher=False
    )

    join_url = f"http://localhost:5173/join/{classroom.join_code}"

    classroom_resp = ClassroomResponse(
        classroom_id=classroom.id,
        room_name=classroom.room_name,
        subject=classroom.subject,
        teacher_name=classroom.teacher_name,
        join_code=classroom.join_code,
        join_url=join_url,
        livekit_room_name=classroom.livekit_room_name,
        is_active=classroom.is_active,
        created_at=classroom.created_at,
    )

    token_val = token_response.get("token") if isinstance(token_response, dict) else getattr(token_response, "token")
    livekit_url_val = token_response.get("livekit_url") if isinstance(token_response, dict) else getattr(token_response, "livekit_url")

    return StudentJoinResponse(
        classroom=classroom_resp,
        token=token_val,
        livekit_url=livekit_url_val,
        student_id=student.student_id,
        student_name=student.name,
    )
