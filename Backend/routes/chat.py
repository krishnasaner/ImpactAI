"""
ImpactAI — Chat route.

POST /chat  →  sends the user message (with session history) to Groq Cloud AI,
runs the ML severity model for a second opinion, persists the conversation
turn in SQLite, and returns the response.
"""

import json
from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from database import get_db, ChatSessionRow, UserRow
from routes.auth import _resolve_current_user
from schemas import ChatRequest, ChatResponse
from services.groq_client import generate_ai_chat
from services.ml_model import predict_severity, is_model_available

chat_router = APIRouter()

# Maximum number of past turns to include as context (to keep token count sane)
_MAX_HISTORY_TURNS = 10


def _get_optional_user(request: Request, db: Session) -> Optional[UserRow]:
    try:
        return _resolve_current_user(request, db)
    except HTTPException:
        return None


def _build_conversation_history(db: Session, session_id: str) -> list[dict]:
    """
    Retrieve the last N conversation turns for this session so the AI
    can maintain context across messages.
    """
    records = (
        db.query(ChatSessionRow)
        .filter(ChatSessionRow.session_id == session_id)
        .order_by(ChatSessionRow.created_at.desc())
        .limit(_MAX_HISTORY_TURNS)
        .all()
    )

    history = []
    for r in reversed(records):
        history.append({"role": "user", "content": r.request_message})
        history.append({"role": "assistant", "content": json.dumps({
            "text": r.response_text,
            "severity": r.severity,
            "suggestions": json.loads(r.suggestions) if r.suggestions else [],
        })})

    return history


@chat_router.post("/chat", response_model=ChatResponse)
async def create_chat(
    request: ChatRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    user = _get_optional_user(http_request, db)

    if not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message text cannot be empty.",
        )

    # ── 0. Resolve or create session ───────────────────────────────────────
    session_id = request.session_id or str(uuid4())

    # ── 1. Build conversation history for context ──────────────────────────
    history = _build_conversation_history(db, session_id)

    # ── 2. Groq AI response (with history) ─────────────────────────────────
    ai_payload = generate_ai_chat(request.message, history=history)

    # ── 3. ML severity prediction (second opinion) ─────────────────────────
    ml_severity: Optional[str] = None
    ml_confidence: Optional[float] = None
    if is_model_available():
        ml_severity, ml_confidence = predict_severity(request.message)

    # ── 4. Persist to SQLite ───────────────────────────────────────────────
    chat_record = ChatSessionRow(
        session_id=session_id,
        user_id=user.id if user else None,
        user_role=user.role if user else "anonymous",
        request_message=request.message,
        response_text=ai_payload["text"],
        severity=ai_payload["severity"],
        suggestions=json.dumps(ai_payload["suggestions"]),
        ml_severity=ml_severity,
        ml_confidence=ml_confidence,
        created_at=datetime.now(timezone.utc),
    )
    db.add(chat_record)
    db.commit()
    db.refresh(chat_record)

    return ChatResponse(
        id=str(chat_record.id),
        text=ai_payload["text"],
        severity=ai_payload["severity"],
        suggestions=ai_payload["suggestions"],
        session_id=session_id,
        ml_severity=ml_severity,
        ml_confidence=ml_confidence,
        created_at=chat_record.created_at,
    )


@chat_router.get("/chat/history")
def chat_history(
    session_id: Optional[str] = None,
    limit: int = 50,
    http_request: Request = None,
    db: Session = Depends(get_db),
):
    """Return recent chat messages (optionally filtered by session)."""
    query = db.query(ChatSessionRow)
    if session_id:
        query = query.filter(ChatSessionRow.session_id == session_id)
    records = (
        query.order_by(ChatSessionRow.created_at.desc())
        .limit(limit)
        .all()
    )
    items = []
    for r in reversed(records):
        items.append({
            "id": r.id,
            "session_id": r.session_id,
            "request_message": r.request_message,
            "response_text": r.response_text,
            "severity": r.severity,
            "suggestions": json.loads(r.suggestions) if r.suggestions else [],
            "ml_severity": r.ml_severity,
            "ml_confidence": r.ml_confidence,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return {"messages": items, "count": len(items)}
