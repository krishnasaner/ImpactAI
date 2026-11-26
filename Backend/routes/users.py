"""
ImpactAI — User Profile, Preferences, and Data Privacy Routes.

Endpoints:
  GET    /users/profile      → Retrieve current user's profile
  PUT    /users/profile      → Update current user's profile
  GET    /users/preferences  → Retrieve current user's preferences
  PUT    /users/preferences  → Update current user's preferences
  GET    /users/export       → Export complete user data in JSON format (GDPR-style privacy compliance)
  DELETE /users/account      → Permanently delete account and all associated personal data
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from database import (
    AppointmentRow,
    ChatSessionRow,
    JournalEntryRow,
    MessageRow,
    MoodEntryRow,
    NotificationRow,
    RefreshTokenRow,
    ResourceBookmarkRow,
    SessionRow,
    UserPreferencesRow,
    UserProfileRow,
    UserRow,
    WellnessActivityRow,
    WellnessPlanRow,
    get_db,
)
from routes.auth import _resolve_current_user
from schemas import (
    UserPreferencesRequest,
    UserPreferencesResponse,
    UserProfileRequest,
    UserProfileResponse,
)
from services.logging import log_audit_event
from services.rate_limit import rate_limiter

router = APIRouter(prefix="/users", tags=["users"])


def _get_or_create_profile(user: UserRow, db: Session) -> UserProfileRow:
    profile = db.query(UserProfileRow).filter(UserProfileRow.user_id == user.id).first()
    if not profile:
        profile = UserProfileRow(
            user_id=user.id,
            display_name=user.name or user.email.split("@")[0],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def _get_or_create_preferences(user: UserRow, db: Session) -> UserPreferencesRow:
    prefs = db.query(UserPreferencesRow).filter(UserPreferencesRow.user_id == user.id).first()
    if not prefs:
        prefs = UserPreferencesRow(
            user_id=user.id,
            preferred_language="en",
            theme="system",
            email_notifications=1,
            push_notifications=1,
            mood_reminders=1,
            journal_reminders=1,
            anonymous_mode=0,
            data_sharing_consent=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.get("/profile", response_model=UserProfileResponse)
def get_user_profile(
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    profile = _get_or_create_profile(user, db)

    return UserProfileResponse(
        id=profile.id,
        user_id=user.id,
        email=user.email,
        role=user.role or "student",
        name=user.name,
        display_name=profile.display_name,
        phone=profile.phone,
        date_of_birth=profile.date_of_birth,
        university=profile.university,
        major=profile.major,
        student_id=profile.student_id,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        license=profile.license,
        experience=profile.experience,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.put("/profile", response_model=UserProfileResponse)
def update_user_profile(
    request: UserProfileRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    rate_limiter.enforce("profile_update", f"user_{user.id}", 30, 60)
    profile = _get_or_create_profile(user, db)

    if request.display_name is not None:
        profile.display_name = request.display_name.strip()
        user.name = request.display_name.strip()
    if request.phone is not None:
        profile.phone = request.phone.strip()
    if request.date_of_birth is not None:
        profile.date_of_birth = request.date_of_birth.strip()
    if request.university is not None:
        profile.university = request.university.strip()
    if request.major is not None:
        profile.major = request.major.strip()
    if request.student_id is not None:
        profile.student_id = request.student_id.strip()
    if request.bio is not None:
        profile.bio = request.bio.strip()
    if request.avatar_url is not None:
        profile.avatar_url = request.avatar_url.strip()
    if request.license is not None and user.role in ("counselor", "admin"):
        profile.license = request.license.strip()
    if request.experience is not None and user.role in ("counselor", "admin"):
        profile.experience = request.experience.strip()

    profile.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)

    log_audit_event(db, "PROFILE_UPDATE", f"User {user.email} updated profile.", user.id)
    db.commit()

    return UserProfileResponse(
        id=profile.id,
        user_id=user.id,
        email=user.email,
        role=user.role or "student",
        name=user.name,
        display_name=profile.display_name,
        phone=profile.phone,
        date_of_birth=profile.date_of_birth,
        university=profile.university,
        major=profile.major,
        student_id=profile.student_id,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        license=profile.license,
        experience=profile.experience,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get("/preferences", response_model=UserPreferencesResponse)
def get_user_preferences(
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    prefs = _get_or_create_preferences(user, db)

    return UserPreferencesResponse(
        user_id=user.id,
        preferred_language=prefs.preferred_language or "en",
        theme=prefs.theme or "system",
        email_notifications=bool(prefs.email_notifications),
        push_notifications=bool(prefs.push_notifications),
        mood_reminders=bool(prefs.mood_reminders),
        journal_reminders=bool(prefs.journal_reminders),
        anonymous_mode=bool(prefs.anonymous_mode),
        data_sharing_consent=bool(prefs.data_sharing_consent),
    )


@router.put("/preferences", response_model=UserPreferencesResponse)
def update_user_preferences(
    request: UserPreferencesRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    prefs = _get_or_create_preferences(user, db)

    if request.preferred_language is not None:
        prefs.preferred_language = request.preferred_language
    if request.theme is not None:
        prefs.theme = request.theme
    if request.email_notifications is not None:
        prefs.email_notifications = 1 if request.email_notifications else 0
    if request.push_notifications is not None:
        prefs.push_notifications = 1 if request.push_notifications else 0
    if request.mood_reminders is not None:
        prefs.mood_reminders = 1 if request.mood_reminders else 0
    if request.journal_reminders is not None:
        prefs.journal_reminders = 1 if request.journal_reminders else 0
    if request.anonymous_mode is not None:
        prefs.anonymous_mode = 1 if request.anonymous_mode else 0
    if request.data_sharing_consent is not None:
        prefs.data_sharing_consent = 1 if request.data_sharing_consent else 0

    prefs.updated_at = datetime.now(timezone.utc)
    db.commit()

    return UserPreferencesResponse(
        user_id=user.id,
        preferred_language=prefs.preferred_language,
        theme=prefs.theme,
        email_notifications=bool(prefs.email_notifications),
        push_notifications=bool(prefs.push_notifications),
        mood_reminders=bool(prefs.mood_reminders),
        journal_reminders=bool(prefs.journal_reminders),
        anonymous_mode=bool(prefs.anonymous_mode),
        data_sharing_consent=bool(prefs.data_sharing_consent),
    )


@router.get("/export")
def export_user_data(
    http_request: Request,
    db: Session = Depends(get_db),
):
    """
    Export all personal data belonging to the user in clean JSON format.
    Ensures complete user privacy and self-service data portability.
    """
    user = _resolve_current_user(http_request, db)
    rate_limiter.enforce("data_export", f"user_{user.id}", 3, 300)

    profile = db.query(UserProfileRow).filter(UserProfileRow.user_id == user.id).first()
    preferences = db.query(UserPreferencesRow).filter(UserPreferencesRow.user_id == user.id).first()
    moods = db.query(MoodEntryRow).filter(MoodEntryRow.user_id == user.id).all()
    journals = db.query(JournalEntryRow).filter(JournalEntryRow.user_id == user.id).all()
    plans = db.query(WellnessPlanRow).filter(WellnessPlanRow.user_id == user.id).all()
    plan_ids = [p.id for p in plans]
    activities = db.query(WellnessActivityRow).filter(WellnessActivityRow.plan_id.in_(plan_ids)).all() if plan_ids else []
    chat_sessions = db.query(ChatSessionRow).filter(ChatSessionRow.user_id == user.id).all()
    session_ids = [s.session_id for s in chat_sessions]
    messages = db.query(MessageRow).filter(MessageRow.chat_session_id.in_(session_ids)).all() if session_ids else []
    appointments = db.query(AppointmentRow).filter(AppointmentRow.student_id == user.id).all()

    export_payload: Dict[str, Any] = {
        "export_metadata": {
            "platform": "ImpactAI Student Mental Wellness",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "user_id": user.id,
            "email": user.email,
        },
        "profile": {
            "name": user.name,
            "display_name": profile.display_name if profile else None,
            "university": profile.university if profile else None,
            "major": profile.major if profile else None,
            "bio": profile.bio if profile else None,
        },
        "preferences": {
            "preferred_language": preferences.preferred_language if preferences else "en",
            "theme": preferences.theme if preferences else "system",
            "anonymous_mode": bool(preferences.anonymous_mode) if preferences else False,
        },
        "mood_history": [
            {
                "id": m.id,
                "mood": m.mood,
                "note": m.note,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in moods
        ],
        "journal_entries": [
            {
                "id": j.id,
                "title": j.title,
                "content": j.content,
                "mood_score": j.mood_score,
                "tags": json.loads(j.tags) if j.tags else [],
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in journals
        ],
        "wellness_plans": [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "status": p.status,
                "activities": [
                    {
                        "title": a.title,
                        "frequency": a.frequency,
                        "progress": a.progress,
                        "completed": bool(a.completed),
                    }
                    for a in activities
                    if a.plan_id == p.id
                ],
            }
            for p in plans
        ],
        "chat_conversations": [
            {
                "session_id": s.session_id,
                "title": s.title,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "messages": [
                    {
                        "sender": m.sender,
                        "content": m.content,
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                    }
                    for m in messages
                    if m.chat_session_id == s.session_id
                ],
            }
            for s in chat_sessions
        ],
        "appointments": [
            {
                "id": a.id,
                "counsellor_id": a.counsellor_id,
                "appointment_date": a.appointment_date.isoformat() if a.appointment_date else None,
                "status": a.status,
                "meeting_type": a.meeting_type,
            }
            for a in appointments
        ],
    }

    log_audit_event(db, "DATA_EXPORT", f"User {user.email} exported personal data.", user.id)
    db.commit()

    return export_payload


@router.delete("/account")
def delete_user_account(
    http_request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Permanently delete the user account and cascade delete all personal records.
    Clears all active sessions, refresh tokens, and cookies.
    """
    user = _resolve_current_user(http_request, db)

    # 1. Cascade cleanup
    db.query(UserProfileRow).filter(UserProfileRow.user_id == user.id).delete()
    db.query(UserPreferencesRow).filter(UserPreferencesRow.user_id == user.id).delete()
    db.query(MoodEntryRow).filter(MoodEntryRow.user_id == user.id).delete()
    db.query(JournalEntryRow).filter(JournalEntryRow.user_id == user.id).delete()
    db.query(WellnessPlanRow).filter(WellnessPlanRow.user_id == user.id).delete()
    db.query(WellnessActivityRow).filter(WellnessActivityRow.user_id == user.id).delete()
    db.query(ResourceBookmarkRow).filter(ResourceBookmarkRow.user_id == user.id).delete()
    db.query(AppointmentRow).filter(AppointmentRow.student_id == user.id).delete()
    db.query(NotificationRow).filter(NotificationRow.user_id == user.id).delete()

    # Chat sessions & messages
    user_sessions = db.query(ChatSessionRow.session_id).filter(ChatSessionRow.user_id == user.id).all()
    session_ids = [s[0] for s in user_sessions]
    if session_ids:
        db.query(MessageRow).filter(MessageRow.chat_session_id.in_(session_ids)).delete(synchronize_session=False)
        db.query(ChatSessionRow).filter(ChatSessionRow.session_id.in_(session_ids)).delete(synchronize_session=False)

    # Auth sessions
    db.query(SessionRow).filter(SessionRow.user_id == user.id).delete()
    db.query(RefreshTokenRow).filter(RefreshTokenRow.user_id == user.id).delete()

    # User record
    log_audit_event(db, "ACCOUNT_DELETE", f"User {user.email} deleted account.", user.id)
    db.delete(user)
    db.commit()

    # Clear auth cookies
    from routes.auth import _clear_auth_cookies
    _clear_auth_cookies(response)

    return {"success": True, "message": "Your account and all associated data have been permanently deleted."}
