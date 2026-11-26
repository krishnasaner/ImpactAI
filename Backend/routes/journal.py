"""
ImpactAI — Private Student Journaling System.

Endpoints:
  POST   /journal         → Create a new journal entry
  GET    /journal         → List authenticated user's journal entries (paginated)
  GET    /journal/search  → Search entries by keyword or date
  GET    /journal/{id}    → Retrieve a single journal entry
  PUT    /journal/{id}    → Update a journal entry
  DELETE /journal/{id}    → Permanently delete a journal entry
"""

import json
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import JournalEntryRow, get_db
from routes.auth import _resolve_current_user
from schemas import JournalCreateRequest, JournalResponse, JournalUpdateRequest
from services.rate_limit import rate_limiter

router = APIRouter(prefix="/journal", tags=["journal"])


def _format_entry(entry: JournalEntryRow) -> JournalResponse:
    parsed_tags = []
    if entry.tags:
        try:
            parsed_tags = json.loads(entry.tags)
            if not isinstance(parsed_tags, list):
                parsed_tags = []
        except Exception:
            parsed_tags = [entry.tags]

    return JournalResponse(
        id=entry.id,
        user_id=entry.user_id,
        title=entry.title,
        content=entry.content,
        mood_score=entry.mood_score,
        tags=parsed_tags,
        is_pinned=bool(entry.is_pinned),
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


@router.post("", response_model=JournalResponse, status_code=status.HTTP_201_CREATED)
def create_journal_entry(
    request: JournalCreateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    rate_limiter.enforce("journal_create", f"user_{user.id}", 30, 60)

    tags_json = json.dumps(request.tags or [])
    entry = JournalEntryRow(
        user_id=user.id,
        title=request.title.strip(),
        content=request.content.strip(),
        mood_score=request.mood_score,
        tags=tags_json,
        is_pinned=1 if request.is_pinned else 0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return _format_entry(entry)


@router.get("", response_model=List[JournalResponse])
def list_journal_entries(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tag: Optional[str] = None,
    http_request: Request = None,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    query = db.query(JournalEntryRow).filter(JournalEntryRow.user_id == user.id)

    if tag:
        query = query.filter(JournalEntryRow.tags.like(f"%{tag}%"))

    # Pinned first, then newest first
    entries = (
        query.order_by(JournalEntryRow.is_pinned.desc(), JournalEntryRow.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [_format_entry(e) for e in entries]


@router.get("/search", response_model=List[JournalResponse])
def search_journal_entries(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(20, ge=1, le=50),
    http_request: Request = None,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    search_term = f"%{q.strip()}%"

    entries = (
        db.query(JournalEntryRow)
        .filter(
            JournalEntryRow.user_id == user.id,
            or_(
                JournalEntryRow.title.like(search_term),
                JournalEntryRow.content.like(search_term),
                JournalEntryRow.tags.like(search_term),
            ),
        )
        .order_by(JournalEntryRow.created_at.desc())
        .limit(limit)
        .all()
    )

    return [_format_entry(e) for e in entries]


@router.get("/{entry_id}", response_model=JournalResponse)
def get_journal_entry(
    entry_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    entry = db.query(JournalEntryRow).filter(JournalEntryRow.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found.")

    if entry.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return _format_entry(entry)


@router.put("/{entry_id}", response_model=JournalResponse)
def update_journal_entry(
    entry_id: int,
    request: JournalUpdateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    entry = db.query(JournalEntryRow).filter(JournalEntryRow.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found.")

    if entry.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if request.title is not None:
        entry.title = request.title.strip()
    if request.content is not None:
        entry.content = request.content.strip()
    if request.mood_score is not None:
        entry.mood_score = request.mood_score
    if request.tags is not None:
        entry.tags = json.dumps(request.tags)
    if request.is_pinned is not None:
        entry.is_pinned = 1 if request.is_pinned else 0

    entry.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(entry)

    return _format_entry(entry)


@router.delete("/{entry_id}")
def delete_journal_entry(
    entry_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _resolve_current_user(http_request, db)
    entry = db.query(JournalEntryRow).filter(JournalEntryRow.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found.")

    if entry.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    db.delete(entry)
    db.commit()

    return {"success": True, "message": "Journal entry deleted successfully."}
