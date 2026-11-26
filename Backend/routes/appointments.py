"""
ImpactAI — Counsellor Profiles & Confidential Student Appointments.

Endpoints:
  GET    /counsellors                  → List verified campus counsellors
  GET    /counsellors/{id}/availability → Get specific counsellor's schedule
  POST   /appointments                 → Book appointment with a counsellor
  GET    /appointments                 → List appointments for current student/counsellor
  PATCH  /appointments/{id}            → Update appointment status or notes
  DELETE /appointments/{id}            → Cancel an appointment
"""

import json
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import AppointmentRow, CounsellorProfileRow, NotificationRow, UserRow, get_db
from routes.auth import _resolve_current_user
from schemas import (
    AppointmentCreateRequest,
    AppointmentResponse,
    AppointmentUpdateRequest,
    CounsellorResponse,
)
from services.logging import log_audit_event
from services.rate_limit import rate_limiter

router = APIRouter(tags=["appointments"])

DEFAULT_COUNSELLORS = [
    {
        "name": "Dr. Sarah Jenkins",
        "title": "Senior Clinical Psychologist",
        "specialties": ["Academic Anxiety", "Depression", "CBT", "Burnout"],
        "languages": ["en"],
        "bio": "Over 12 years supporting college students through high-stress exam periods and emotional transitions.",
        "rating": 4.9,
        "review_count": 48,
        "experience": "12+ years",
        "availability_slots": {
            "monday": ["10:00", "11:00", "14:00", "16:00"],
            "wednesday": ["09:00", "11:00", "15:00"],
            "friday": ["10:00", "13:00", "14:00"],
        },
    },
    {
        "name": "Prof. Rajesh Sharma",
        "title": "Licensed Student Wellness Counselor",
        "specialties": ["Mindfulness", "Life Transitions", "Interpersonal Relationships"],
        "languages": ["en", "hi"],
        "bio": "Specialized in mindfulness-based stress reduction and student identity navigation.",
        "rating": 4.8,
        "review_count": 32,
        "experience": "8+ years",
        "availability_slots": {
            "tuesday": ["10:00", "11:00", "14:00"],
            "thursday": ["10:00", "14:00", "16:00"],
        },
    },
]


def _seed_counsellors_if_empty(db: Session) -> None:
    count = db.query(CounsellorProfileRow).count()
    if count == 0:
        for c in DEFAULT_COUNSELLORS:
            # Check if user exists or create counsellor user
            email = f"{c['name'].lower().replace(' ', '.').replace('dr.', '').replace('prof.', '').strip()}@campus.edu"
            c_user = db.query(UserRow).filter(UserRow.email == email).first()
            if not c_user:
                c_user = UserRow(
                    email=email,
                    hashed_password="$2b$12$N9qo8uLOickgx2ZMRZo5i.ej8E6B7d3n0Q7Yx8qM9Kf6J5M2Aq4wK",
                    role="counselor",
                    name=c["name"],
                    created_at=datetime.now(timezone.utc),
                    is_verified=1,
                )
                db.add(c_user)
                db.flush()

            profile = CounsellorProfileRow(
                user_id=c_user.id,
                name=c["name"],
                title=c["title"],
                specialties=json.dumps(c["specialties"]),
                languages=json.dumps(c["languages"]),
                bio=c["bio"],
                rating=c["rating"],
                review_count=c["review_count"],
                experience=c["experience"],
                is_available=1,
                availability_slots=json.dumps(c["availability_slots"]),
                created_at=datetime.now(timezone.utc),
            )
            db.add(profile)
        db.commit()


def _format_counsellor(c: CounsellorProfileRow) -> CounsellorResponse:
    specialties = json.loads(c.specialties) if c.specialties else []
    languages = json.loads(c.languages) if c.languages else ["en"]
    slots = json.loads(c.availability_slots) if c.availability_slots else {}
    return CounsellorResponse(
        id=c.id,
        user_id=c.user_id,
        name=c.name,
        title=c.title or "Student Counselor",
        specialties=specialties,
        languages=languages,
        bio=c.bio,
        rating=c.rating or 5.0,
        review_count=c.review_count or 0,
        experience=c.experience or "5+ years",
        is_available=bool(c.is_available),
        availability_slots=slots,
    )


def _format_appointment(app: AppointmentRow, db: Session) -> AppointmentResponse:
    c_user = db.query(UserRow).filter(UserRow.id == app.counsellor_id).first()
    s_user = db.query(UserRow).filter(UserRow.id == app.student_id).first()
    return AppointmentResponse(
        id=app.id,
        student_id=app.student_id,
        counsellor_id=app.counsellor_id,
        counsellor_name=c_user.name if c_user else "Campus Counselor",
        student_name=s_user.name if s_user else "Student",
        appointment_date=app.appointment_date,
        duration_minutes=app.duration_minutes or 45,
        status=app.status or "scheduled",
        meeting_type=app.meeting_type or "video",
        notes=app.notes,
        created_at=app.created_at,
    )


@router.get("/counsellors", response_model=List[CounsellorResponse])
def list_counsellors(db: Session = Depends(get_db)):
    _seed_counsellors_if_empty(db)
    counsellors = db.query(CounsellorProfileRow).filter(CounsellorProfileRow.is_available == 1).all()
    return [_format_counsellor(c) for c in counsellors]


@router.get("/counsellors/{counsellor_id}/availability")
def get_counsellor_availability(counsellor_id: int, db: Session = Depends(get_db)):
    _seed_counsellors_if_empty(db)
    c = db.query(CounsellorProfileRow).filter(CounsellorProfileRow.id == counsellor_id).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Counsellor not found.")

    slots = json.loads(c.availability_slots) if c.availability_slots else {}
    return {
        "counsellor_id": c.id,
        "name": c.name,
        "is_available": bool(c.is_available),
        "weekly_slots": slots,
    }


@router.post("/appointments", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def book_appointment(
    request: AppointmentCreateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    rate_limiter.enforce("appointment_book", f"user_{user.id}", 10, 300)

    # Check counsellor exists by profile id, profile user_id, or direct UserRow id
    c_profile = (
        db.query(CounsellorProfileRow)
        .filter(
            or_(
                CounsellorProfileRow.id == request.counsellor_id,
                CounsellorProfileRow.user_id == request.counsellor_id,
            )
        )
        .first()
    )
    if c_profile:
        counsellor_user_id = c_profile.user_id
        counsellor_name = c_profile.name
    else:
        c_user = db.query(UserRow).filter(UserRow.id == request.counsellor_id, UserRow.role.in_(("counselor", "admin"))).first()
        if not c_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Selected counsellor not found.")
        counsellor_user_id = c_user.id
        counsellor_name = c_user.name

    # Avoid duplicate booking at identical time
    existing = (
        db.query(AppointmentRow)
        .filter(
            AppointmentRow.counsellor_id == counsellor_user_id,
            AppointmentRow.appointment_date == request.appointment_date,
            AppointmentRow.status == "scheduled",
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This appointment slot is already reserved. Please select another time.",
        )

    appointment = AppointmentRow(
        student_id=user.id,
        counsellor_id=counsellor_user_id,
        appointment_date=request.appointment_date,
        duration_minutes=request.duration_minutes or 45,
        status="scheduled",
        meeting_type=request.meeting_type or "video",
        notes=request.notes.strip() if request.notes else None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(appointment)

    # Create notification for student
    db.add(NotificationRow(
        user_id=user.id,
        title="Counseling Session Confirmed",
        message=f"Your counseling appointment with {counsellor_name} is scheduled for {request.appointment_date.strftime('%b %d, %Y at %I:%M %p')}.",
        type="appointment",
        link="/app/booking",
        created_at=datetime.now(timezone.utc),
    ))

    # Create notification for counsellor
    db.add(NotificationRow(
        user_id=counsellor_user_id,
        title="New Student Appointment",
        message=f"New appointment booked for {request.appointment_date.strftime('%b %d at %I:%M %p')}.",
        type="appointment",
        link="/app/admin-dashboard",
        created_at=datetime.now(timezone.utc),
    ))

    log_audit_event(db, "APPOINTMENT_BOOK", f"Student {user.email} booked appointment with {counsellor_name}.", user.id)
    db.commit()
    db.refresh(appointment)

    return _format_appointment(appointment, db)


@router.get("/appointments", response_model=List[AppointmentResponse])
def list_appointments(
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)

    if user.role in ("counselor", "admin"):
        query = db.query(AppointmentRow).filter(AppointmentRow.counsellor_id == user.id)
    else:
        query = db.query(AppointmentRow).filter(AppointmentRow.student_id == user.id)

    appointments = query.order_by(AppointmentRow.appointment_date.desc()).all()
    return [_format_appointment(a, db) for a in appointments]


@router.patch("/appointments/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    request: AppointmentUpdateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    app = db.query(AppointmentRow).filter(AppointmentRow.id == appointment_id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

    # Access check
    if user.id != app.student_id and user.id != app.counsellor_id and user.role not in ("admin", "counselor"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if request.status is not None:
        app.status = request.status
    if request.counsellor_notes is not None and user.role in ("counselor", "admin"):
        app.counsellor_notes = request.counsellor_notes.strip()

    app.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(app)
    return _format_appointment(app, db)


@router.delete("/appointments/{appointment_id}")
def cancel_appointment(
    appointment_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    app = db.query(AppointmentRow).filter(AppointmentRow.id == appointment_id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

    if user.id != app.student_id and user.id != app.counsellor_id and user.role not in ("admin", "counselor"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    app.status = "cancelled"
    app.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"success": True, "message": "Appointment cancelled successfully."}
