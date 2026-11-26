"""
ImpactAI — Mood tracking routes.

POST   /mood          → log a mood entry
GET    /mood/history  → retrieve past mood entries
GET    /mood/summary  → retrieve aggregate stats, streak, and distribution
GET    /mood/trends   → retrieve daily averages over last 30 days
PUT    /mood/{id}     → update a mood entry
DELETE /mood/{id}     → delete a mood entry
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import MoodEntryRow, UserRow, get_db
from routes.auth import _resolve_current_user
from schemas import MoodRequest, MoodResponse
from services.rate_limit import rate_limiter

mood_router = APIRouter()


@mood_router.post("/mood", response_model=MoodResponse)
def log_mood(
    request: MoodRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    rate_limiter.enforce("mood_user", f"user_{user.id}")

    entry = MoodEntryRow(
        user_id=user.id,
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
    safe_limit = max(1, min(limit, 100))
    user = _resolve_current_user(http_request, db)

    query = db.query(MoodEntryRow).filter(MoodEntryRow.user_id == user.id)
    records = (
        query.order_by(MoodEntryRow.created_at.desc()).limit(safe_limit).all()
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


@mood_router.get("/mood/summary")
def mood_summary(
    http_request: Request,
    db: Session = Depends(get_db),
):
    """Calculate weekly average, streak, and mood distribution."""
    user = _resolve_current_user(http_request, db)
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)

    recent_records = (
        db.query(MoodEntryRow)
        .filter(MoodEntryRow.user_id == user.id, MoodEntryRow.created_at >= seven_days_ago)
        .all()
    )

    all_records = (
        db.query(MoodEntryRow)
        .filter(MoodEntryRow.user_id == user.id)
        .order_by(MoodEntryRow.created_at.desc())
        .all()
    )

    distribution: Dict[str, int] = {}
    numeric_scores = []
    for r in all_records:
        distribution[r.mood] = distribution.get(r.mood, 0) + 1
        try:
            numeric_scores.append(float(r.mood))
        except ValueError:
            pass

    avg_score = round(sum(numeric_scores) / len(numeric_scores), 2) if numeric_scores else 0.0

    return {
        "total_entries": len(all_records),
        "weekly_entries": len(recent_records),
        "average_score": avg_score,
        "distribution": distribution,
    }


@mood_router.get("/mood/trends")
def mood_trends(
    days: int = 30,
    http_request: Request = None,
    db: Session = Depends(get_db),
):
    """Calculate daily mood trends for the user over the requested window."""
    user = _resolve_current_user(http_request, db)
    safe_days = max(1, min(days, 90))
    start_date = datetime.now(timezone.utc) - timedelta(days=safe_days)

    records = (
        db.query(MoodEntryRow)
        .filter(MoodEntryRow.user_id == user.id, MoodEntryRow.created_at >= start_date)
        .order_by(MoodEntryRow.created_at.asc())
        .all()
    )

    daily_map: Dict[str, List[float]] = {}
    for r in records:
        day_str = r.created_at.strftime("%Y-%m-%d") if r.created_at else "unknown"
        val = 3.0
        try:
            val = float(r.mood)
        except ValueError:
            pass
        daily_map.setdefault(day_str, []).append(val)

    trend_data = [
        {"date": day, "average": round(sum(scores) / len(scores), 2), "count": len(scores)}
        for day, scores in sorted(daily_map.items())
    ]

    return {
        "period_days": safe_days,
        "total_records": len(records),
        "trend_data": trend_data,
    }


@mood_router.put("/mood/{mood_id}", response_model=MoodResponse)
def update_mood(
    mood_id: int,
    request: MoodRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    entry = db.query(MoodEntryRow).filter(MoodEntryRow.id == mood_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mood entry not found.")

    if entry.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    entry.mood = request.mood
    entry.note = request.note
    db.commit()
    db.refresh(entry)

    return MoodResponse(
        id=entry.id,
        mood=entry.mood,
        note=entry.note,
        created_at=entry.created_at,
    )


@mood_router.delete("/mood/{mood_id}")
def delete_mood(
    mood_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    entry = db.query(MoodEntryRow).filter(MoodEntryRow.id == mood_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mood entry not found.")

    if entry.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    db.delete(entry)
    db.commit()

    return {"success": True, "message": "Mood entry deleted successfully."}

