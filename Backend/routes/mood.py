"""
ImpactAI — Mood tracking routes.

POST /mood          →  log a mood entry
GET  /mood/history  →  retrieve past mood entries
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from database import get_db, MoodEntryRow, UserRow
from routes.auth import _resolve_current_user
from schemas import MoodRequest, MoodResponse

mood_router = APIRouter()


def _get_optional_user(request: Request, db: Session) -> Optional[UserRow]:
    try:
        return _resolve_current_user(request, db)
    except HTTPException:
        return None


@mood_router.post("/mood", response_model=MoodResponse)
def log_mood(
    request: MoodRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _get_optional_user(http_request, db)

    entry = MoodEntryRow(
        user_id=user.id if user else None,
        mood=request.mood,
        note=request.note,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return MoodResponse(
        id=entry.id,
        mood=entry.mood,
        note=entry.note,
        created_at=entry.created_at,
    )


@mood_router.get("/mood/history")
def mood_history(
    limit: int = 30,
    http_request: Request = None,
    db: Session = Depends(get_db),
):
    user = _get_optional_user(http_request, db) if http_request else None

    query = db.query(MoodEntryRow)
    if user:
        query = query.filter(MoodEntryRow.user_id == user.id)

    records = (
        query.order_by(MoodEntryRow.created_at.desc()).limit(limit).all()
    )
    return {
        "moods": [
            {
                "id": r.id,
                "mood": r.mood,
                "note": r.note,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reversed(records)
        ],
        "count": len(records),
    }
