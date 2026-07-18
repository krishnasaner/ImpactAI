"""
ImpactAI — Chat route.

POST /chat  →  sends the user message (with session history) to Groq Cloud AI,
runs the ML severity model for a second opinion, persists the conversation
turn in SQLite, and returns the response.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from database import get_db, ChatSessionRow, UserRow, MessageRow
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
    Retrieve the last N conversation turns for this session from MessageRow
    so the AI can maintain context across messages.
    """
    records = (
        db.query(MessageRow)
        .filter(MessageRow.chat_session_id == session_id)
        .order_by(MessageRow.created_at.desc())
        .limit(_MAX_HISTORY_TURNS * 2)
        .all()
    )

    history = []
    # records are retrieved newest-first; we reverse it to maintain chronological order
    for r in reversed(records):
        if r.sender == "user":
            history.append({"role": "user", "content": r.content})
        else:
            history.append(
                {
                    "role": "assistant",
                    "content": json.dumps(
                        {
                            "text": r.content,
                            "severity": r.llm_severity or "low",
                            "suggestions": json.loads(r.suggestions)
                            if r.suggestions
                            else [],
                        }
                    ),
                }
            )

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

    # Resolve active chat session in DB
    chat_session = db.query(ChatSessionRow).filter(ChatSessionRow.session_id == session_id).first()
    if not chat_session:
        chat_session = ChatSessionRow(
            session_id=session_id,
            user_id=user.id if user else None,
            user_role=user.role if user else "anonymous",
            created_at=datetime.now(timezone.utc),
        )
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)

    # ── 1. Build conversation history for context ──────────────────────────
    history = _build_conversation_history(db, session_id)

    # ── 2. Groq AI response (with history) ─────────────────────────────────
    try:
        ai_payload = await asyncio.to_thread(
            generate_ai_chat, request.message, history
        )
    except RuntimeError as exc:
        logger.error("Groq API configuration error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured. Please set GROQ_API_KEY.",
        )
    except Exception as exc:
        logger.error("Groq API call failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service temporarily unavailable. Please try again.",
        )

    # ── 3. ML severity prediction (second opinion) ─────────────────────────
    ml_severity: Optional[str] = None
    ml_confidence: Optional[float] = None
    try:
        if is_model_available():
            ml_severity, ml_confidence = predict_severity(request.message)
    except Exception as exc:
        logger.warning("ML severity prediction failed: %s", exc)

    # ── 4. Persist turns as messages to SQLite ─────────────────────────────
    # User message
    user_msg = MessageRow(
        chat_session_id=session_id,
        sender="user",
        content=request.message,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user_msg)

    # Assistant message
    assistant_msg = MessageRow(
        chat_session_id=session_id,
        sender="assistant",
        content=ai_payload["text"],
        ml_severity=ml_severity,
        ml_confidence=ml_confidence,
        llm_severity=ai_payload["severity"],
        suggestions=json.dumps(ai_payload["suggestions"]),
        created_at=datetime.now(timezone.utc),
    )
    db.add(assistant_msg)

    # Update backward-compatible ChatSessionRow properties
    chat_session.request_message = request.message
    chat_session.response_text = ai_payload["text"]
    chat_session.severity = ai_payload["severity"]
    chat_session.suggestions = json.dumps(ai_payload["suggestions"])
    chat_session.ml_severity = ml_severity
    chat_session.ml_confidence = ml_confidence

    db.commit()

    return ChatResponse(
        id=str(assistant_msg.id),
        text=ai_payload["text"],
        severity=ai_payload["severity"],
        suggestions=ai_payload["suggestions"],
        session_id=session_id,
        ml_severity=ml_severity,
        ml_confidence=ml_confidence,
        created_at=assistant_msg.created_at,
    )


@chat_router.get("/chat/history")
def chat_history(
    session_id: Optional[str] = None,
    limit: int = 50,
    http_request: Request = None,
    db: Session = Depends(get_db),
):
    """Return recent chat messages for the authenticated user."""
    user = _resolve_current_user(http_request, db)
    query = db.query(MessageRow)
    if session_id:
        chat_session = db.query(ChatSessionRow).filter(ChatSessionRow.session_id == session_id).first()
        if not chat_session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found.")
        if user.role not in ("admin", "counselor") and chat_session.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        query = query.filter(MessageRow.chat_session_id == session_id)
    elif user.role not in ("admin", "counselor"):
        session_ids = (
            db.query(ChatSessionRow.session_id)
            .filter(ChatSessionRow.user_id == user.id)
            .subquery()
        )
        query = query.filter(MessageRow.chat_session_id.in_(session_ids))
    records = (
        query.order_by(MessageRow.created_at.desc())
        .limit(min(limit, 100))
        .all()
    )
    items = []
    for r in reversed(records):
        items.append(
            {
                "id": r.id,
                "session_id": r.chat_session_id,
                "sender": r.sender,
                "content": r.content,
                "ml_severity": r.ml_severity,
                "ml_confidence": r.ml_confidence,
                "llm_severity": r.llm_severity,
                "suggestions": json.loads(r.suggestions) if r.suggestions else [],
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )
    return {"messages": items, "count": len(items)}
