"""
ImpactAI — Administrative Dashboard and Governance Analytics.

Endpoints:
  GET /admin/dashboard     → Comprehensive KPI overview for student wellness & risk triage
  GET /admin/users         → Paginated student/counsellor user list
  GET /admin/analytics     → Mental health trends, session volumes & risk levels
  GET /admin/system-health → Comprehensive health audit of DB, ML & Cloud AI
  GET /admin/audit-logs    → Paginated security & administrative audit trails
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import GROQ_API_KEY, GROQ_MODEL
from database import (
    AppointmentRow,
    AuditLogRow,
    ChatSessionRow,
    JournalEntryRow,
    MessageRow,
    MoodEntryRow,
    SecurityLogRow,
    UserRow,
    get_db,
)
from routes.auth import _resolve_current_user
from services.ml_model import is_model_available

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin_or_counselor(request: Request, db: Session) -> UserRow:
    user = _resolve_current_user(request, db)
    if user.role not in ("admin", "counselor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Administrators and Counselors only.",
        )
    return user


@router.get("/dashboard")
def get_admin_dashboard(
    http_request: Request,
    db: Session = Depends(get_db),
):
    _require_admin_or_counselor(http_request, db)

    now = datetime.now(timezone.utc)
    twenty_four_hours_ago = now - timedelta(hours=24)
    seven_days_ago = now - timedelta(days=7)

    total_users = db.query(func.count(UserRow.id)).scalar() or 0
    total_students = db.query(func.count(UserRow.id)).filter(UserRow.role == "student").scalar() or 0
    total_counselors = db.query(func.count(UserRow.id)).filter(UserRow.role == "counselor").scalar() or 0

    active_24h = db.query(func.count(UserRow.id)).filter(UserRow.last_login_at >= twenty_four_hours_ago).scalar() or 0
    total_chats = db.query(func.count(ChatSessionRow.id)).scalar() or 0
    total_messages = db.query(func.count(MessageRow.id)).scalar() or 0
    total_moods = db.query(func.count(MoodEntryRow.id)).scalar() or 0
    total_journals = db.query(func.count(JournalEntryRow.id)).scalar() or 0
    total_appointments = db.query(func.count(AppointmentRow.id)).scalar() or 0

    # Risk level distribution across sessions
    severity_breakdown = {}
    sev_rows = (
        db.query(ChatSessionRow.severity, func.count(ChatSessionRow.id))
        .group_by(ChatSessionRow.severity)
        .all()
    )
    for sev, cnt in sev_rows:
        severity_breakdown[sev or "unknown"] = cnt

    # Crisis events in last 7 days
    crisis_recent = (
        db.query(func.count(ChatSessionRow.id))
        .filter(ChatSessionRow.severity == "crisis", ChatSessionRow.created_at >= seven_days_ago)
        .scalar()
        or 0
    )

    # Active appointments
    scheduled_appointments = (
        db.query(func.count(AppointmentRow.id))
        .filter(AppointmentRow.status == "scheduled", AppointmentRow.appointment_date >= now)
        .scalar()
        or 0
    )

    return {
        "user_metrics": {
            "total_users": total_users,
            "total_students": total_students,
            "total_counselors": total_counselors,
            "active_users_24h": active_24h,
        },
        "engagement_metrics": {
            "total_chat_sessions": total_chats,
            "total_messages": total_messages,
            "total_mood_checkins": total_moods,
            "total_journal_entries": total_journals,
            "total_appointments": total_appointments,
            "upcoming_appointments": scheduled_appointments,
        },
        "safety_metrics": {
            "severity_distribution": severity_breakdown,
            "recent_crisis_sessions_7d": crisis_recent,
        },
    }


@router.get("/users")
def list_admin_users(
    role: Optional[str] = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    http_request: Request = None,
    db: Session = Depends(get_db),
):
    _require_admin_or_counselor(http_request, db)

    query = db.query(UserRow)
    if role:
        query = query.filter(UserRow.role == role)

    total = query.count()
    users = query.order_by(UserRow.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "role": u.role,
                "name": u.name,
                "is_verified": bool(u.is_verified),
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
    }


@router.get("/system-health")
def get_system_health(
    http_request: Request,
    db: Session = Depends(get_db),
):
    _require_admin_or_counselor(http_request, db)

    db_ok = True
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1")).scalar()
    except Exception:
        db_ok = False

    ml_ok = is_model_available()
    ai_status = "configured" if bool(GROQ_API_KEY) else "local_fallback"

    return {
        "status": "healthy" if db_ok and ml_ok else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {
            "engine": "SQLite WAL",
            "status": "reachable" if db_ok else "unreachable",
        },
        "ml_pipeline": {
            "status": "loaded" if ml_ok else "offline",
            "architecture": "TF-IDF + Logistic Regression",
        },
        "ai_cloud": {
            "provider": "Groq Cloud API",
            "model": GROQ_MODEL,
            "status": ai_status,
        },
    }


@router.get("/audit-logs")
def list_audit_logs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    http_request: Request = None,
    db: Session = Depends(get_db),
):
    _require_admin_or_counselor(http_request, db)

    logs = db.query(AuditLogRow).order_by(AuditLogRow.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "count": len(logs),
        "logs": [
            {
                "id": l.id,
                "action": l.action,
                "user_id": l.user_id,
                "description": l.description,
                "ip_address": l.ip_address,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
    }
