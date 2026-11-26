"""
ImpactAI — Chat route and Layered Mental Health Triage.

POST /chat  →  Processes user message through a layered safety pipeline:
  1. Input validation & length limits
  2. Session ownership resolution
  3. Deterministic crisis detection (safety rules)
  4. Local ML severity prediction
  5. Context-aware AI generation (Groq Llama-3)
  6. Conservative safety resolution (crisis cannot be downgraded)
  7. Atomic SQLite persistence

GET /chat/history  →  Returns conversation history with strict IDOR access control.
GET /chat/sessions →  Returns user's active/past chat sessions.
DELETE /chat/session/{session_id} → Deletes a chat session for the authenticated user.
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from database import ChatSessionRow, MessageRow, UserRow, get_db
from routes.auth import _resolve_current_user
from schemas import ChatRequest, ChatResponse
from services.groq_client import generate_ai_chat, generate_ai_chat_async
from services.ml_model import is_model_available, predict_severity
from services.rate_limit import rate_limiter

logger = logging.getLogger(__name__)

chat_router = APIRouter()

_MAX_HISTORY_TURNS = 10
_MAX_MESSAGE_LENGTH = 3000

# ── Deterministic Crisis Signal Patterns ─────────────────────────────────────
# These patterns capture explicit high-risk expressions that MUST NOT be
# downgraded by any statistical model or LLM.
DETERMINISTIC_CRISIS_PATTERNS = [
    r"\bsuicid\w*\b",
    r"\bkill(ing)?\s+(my|it|one)?self\b",
    r"\bend(ing)?\s+(my\s+life|it\s+all|my|it|life)\b",
    r"\bwant(ing)?\s+to\s+die\b",
    r"\bdon'?t\s+want\s+to\s+live\b",
    r"\bhang(ing)?\s+(my|one)?self\b",
    r"\bcut(ting)?\s+(my\s+)?(wrists?|arms?|throat)\b",
    r"\boverdos\w*\b",
    r"\btak(e|ing)\s+all\s+(my\s+)?pills\b",
    r"\bjump(ing)?\s+off\s+(a\s+)?(bridge|roof|building)\b",
    r"\bshoot(ing)?\s+myself\b",
    r"\bbetter\s+off\s+dead\b",
    r"\bno\s+reason\s+to\s+live\b",
]

_CRISIS_REGEX = re.compile("|".join(DETERMINISTIC_CRISIS_PATTERNS), re.IGNORECASE)


def detect_deterministic_crisis(text: str) -> bool:
    """Return True if explicit crisis language is detected deterministically."""
    return bool(_CRISIS_REGEX.search(text))


def _get_optional_user(request: Request, db: Session) -> Optional[UserRow]:
    try:
        return _resolve_current_user(request, db)
    except HTTPException:
        return None


def _build_conversation_history(db: Session, session_id: str) -> List[Dict[str, str]]:
    """
    Retrieve the last N conversation turns for this session.
    Assistant turns are stored as clean conversational text (not JSON strings),
    allowing the LLM to understand natural conversational context without pollution.
    """
    records = (
        db.query(MessageRow)
        .filter(MessageRow.chat_session_id == session_id)
        .order_by(MessageRow.created_at.desc())
        .limit(_MAX_HISTORY_TURNS * 2)
        .all()
    )

    history: List[Dict[str, str]] = []
    # records are retrieved newest-first; reverse to chronological order
    for r in reversed(records):
        role = "user" if r.sender == "user" else "assistant"
        history.append({"role": role, "content": r.content})

    return history


@chat_router.post("/chat", response_model=ChatResponse)
async def create_chat(
    request: ChatRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    """
    Process incoming chat message with layered crisis detection,
    Groq AI generation, ML severity validation, and atomic persistence.
    """
    user = _get_optional_user(http_request, db)

    # Rate limiting
    client_key = f"user_{user.id}" if user else f"ip_{http_request.client.host if http_request.client else 'unknown'}"
    rate_limiter.enforce("chat_user", client_key)

    # 1. Input Validation
    raw_message = request.message.strip()
    if not raw_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message text cannot be empty.",
        )
    if len(raw_message) > _MAX_MESSAGE_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Message exceeds maximum allowed length of {_MAX_MESSAGE_LENGTH} characters.",
        )

    # 2. Resolve or create chat session
    session_id = request.session_id or str(uuid4())

    chat_session = (
        db.query(ChatSessionRow)
        .filter(ChatSessionRow.session_id == session_id)
        .first()
    )
    if not chat_session:
        session_title = raw_message[:40] + ("..." if len(raw_message) > 40 else "")
        chat_session = ChatSessionRow(
            session_id=session_id,
            title=session_title,
            user_id=user.id if user else None,
            user_role=user.role if user else "anonymous",
            created_at=datetime.now(timezone.utc),
        )
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)
    else:
        # Enforce strict session ownership and IDOR isolation
        if chat_session.user_id is not None:
            if not user or user.id != chat_session.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: chat session belongs to another user.",
                )
        else:
            # Associate guest session with newly authenticated user
            if user:
                chat_session.user_id = user.id
                chat_session.user_role = user.role
                db.commit()

    # 3. Layered Safety Analysis
    # Layer A: Deterministic Rule Check
    is_crisis_deterministic = detect_deterministic_crisis(raw_message)

    # Layer B: Local ML Severity Classifier
    ml_severity: Optional[str] = None
    ml_confidence: Optional[float] = None
    try:
        if is_model_available():
            ml_severity, ml_confidence = predict_severity(raw_message)
    except Exception as exc:
        logger.warning("ML severity prediction failed: %s", exc)

    # 4. Context Retrieval (clean text, not JSON)
    history = _build_conversation_history(db, session_id)

    # 5. Groq Cloud AI Generation
    try:
        if asyncio.iscoroutinefunction(generate_ai_chat):
            ai_payload = await generate_ai_chat(
                raw_message,
                history=history,
                is_crisis=is_crisis_deterministic,
            )
        else:
            res = generate_ai_chat(
                raw_message,
                history=history,
                is_crisis=is_crisis_deterministic,
            )
            if asyncio.iscoroutine(res):
                ai_payload = await res
            else:
                ai_payload = res
    except Exception as exc:
        logger.error("AI Generation error: %s", exc)
        from services.groq_client import get_fallback
        ai_payload = get_fallback("service_error", is_crisis=is_crisis_deterministic)

    # 6. Conservative Safety Resolution
    # Rule: If deterministic rules trigger crisis, LLM or ML cannot downgrade it.
    llm_severity = ai_payload.get("severity", "low")
    if is_crisis_deterministic:
        final_severity = "crisis"
    elif llm_severity == "crisis" or ml_severity == "crisis":
        final_severity = "crisis"
    elif llm_severity == "high" or ml_severity == "high":
        final_severity = "high"
    elif llm_severity == "medium" or ml_severity == "medium":
        final_severity = "medium"
    else:
        final_severity = "low"

    # Ensure final severity is reflected in the payload
    ai_payload["severity"] = final_severity

    # 7. Atomic Database Persistence
    try:
        user_msg = MessageRow(
            chat_session_id=session_id,
            sender="user",
            content=raw_message,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user_msg)

        assistant_msg = MessageRow(
            chat_session_id=session_id,
            sender="assistant",
            content=ai_payload["text"],
            ml_severity=ml_severity,
            ml_confidence=ml_confidence,
            llm_severity=final_severity,
            suggestions=json.dumps(ai_payload["suggestions"]),
            created_at=datetime.now(timezone.utc),
        )
        db.add(assistant_msg)

        # Update chat session summary
        chat_session.request_message = raw_message
        chat_session.response_text = ai_payload["text"]
        chat_session.severity = final_severity
        chat_session.suggestions = json.dumps(ai_payload["suggestions"])
        chat_session.ml_severity = ml_severity
        chat_session.ml_confidence = ml_confidence

        db.commit()
        db.refresh(assistant_msg)

    except Exception as db_err:
        db.rollback()
        logger.error("Failed to persist chat message: %s", db_err, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save conversation state.",
        )

    return ChatResponse(
        id=str(assistant_msg.id),
        text=ai_payload["text"],
        severity=final_severity,
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
    """Return recent chat messages with strict access control and IDOR prevention."""
    safe_limit = max(1, min(limit, 100))
    user = _get_optional_user(http_request, db) if http_request else None

    if not session_id:
        if not user:
            return {"messages": [], "count": 0}

        if user.role in ("admin", "counselor"):
            query = db.query(MessageRow)
        else:
            user_session_tuples = (
                db.query(ChatSessionRow.session_id)
                .filter(ChatSessionRow.user_id == user.id)
                .all()
            )
            user_session_ids = [s[0] for s in user_session_tuples]
            if not user_session_ids:
                return {"messages": [], "count": 0}
            query = db.query(MessageRow).filter(MessageRow.chat_session_id.in_(user_session_ids))
    else:
        chat_session = (
            db.query(ChatSessionRow)
            .filter(ChatSessionRow.session_id == session_id)
            .first()
        )
        if not chat_session:
            return {"messages": [], "count": 0}

        if chat_session.user_id is not None:
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required to access this chat session.",
                )
            if user.id != chat_session.user_id and user.role not in ("admin", "counselor"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: chat session belongs to another user.",
                )

        query = db.query(MessageRow).filter(MessageRow.chat_session_id == session_id)

    records = (
        query.order_by(MessageRow.created_at.desc())
        .limit(safe_limit)
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


@chat_router.get("/chat/sessions")
def list_chat_sessions(
    limit: int = 20,
    http_request: Request = None,
    db: Session = Depends(get_db),
):
    """List recent chat sessions belonging to the current user."""
    safe_limit = max(1, min(limit, 50))
    user = _get_optional_user(http_request, db) if http_request else None
    if not user:
        return {"sessions": [], "count": 0}

    sessions = (
        db.query(ChatSessionRow)
        .filter(ChatSessionRow.user_id == user.id)
        .order_by(ChatSessionRow.created_at.desc())
        .limit(safe_limit)
        .all()
    )

    return {
        "sessions": [
            {
                "session_id": s.session_id,
                "title": getattr(s, "title", None) or "Conversation",
                "last_message": s.request_message,
                "severity": s.severity,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sessions
        ],
        "count": len(sessions),
    }


@chat_router.delete("/chat/session/{session_id}")
def delete_chat_session(
    session_id: str,
    http_request: Request,
    db: Session = Depends(get_db),
):
    """Delete a chat session and associated messages, verifying user ownership."""
    user = _get_optional_user(http_request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    chat_session = (
        db.query(ChatSessionRow)
        .filter(ChatSessionRow.session_id == session_id)
        .first()
    )
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    if chat_session.user_id != user.id and user.role not in ("admin", "counselor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    db.query(MessageRow).filter(MessageRow.chat_session_id == session_id).delete()
    db.delete(chat_session)
    db.commit()

    return {"success": True, "message": "Chat session deleted successfully."}


@chat_router.patch("/chat/sessions/{session_id}")
def rename_chat_session(
    session_id: str,
    request: Dict[str, str],
    http_request: Request,
    db: Session = Depends(get_db),
):
    """Rename a chat conversation title."""
    user = _get_optional_user(http_request, db)
    chat_session = db.query(ChatSessionRow).filter(ChatSessionRow.session_id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found.")

    if chat_session.user_id is not None:
        if not user or user.id != chat_session.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    new_title = request.get("title", "").strip()
    if not new_title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title cannot be empty.")

    chat_session.title = new_title[:100]
    db.commit()
    return {"success": True, "session_id": session_id, "title": chat_session.title}


@chat_router.get("/chat/sessions/{session_id}/messages")
def get_session_messages(
    session_id: str,
    limit: int = 50,
    offset: int = 0,
    http_request: Request = None,
    db: Session = Depends(get_db),
):
    """Paginated retrieval of messages for a specific session."""
    user = _get_optional_user(http_request, db) if http_request else None
    chat_session = db.query(ChatSessionRow).filter(ChatSessionRow.session_id == session_id).first()
    if not chat_session:
        return {"messages": [], "count": 0, "total": 0}

    if chat_session.user_id is not None:
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
        if user.id != chat_session.user_id and user.role not in ("admin", "counselor"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    safe_limit = max(1, min(limit, 100))
    query = db.query(MessageRow).filter(MessageRow.chat_session_id == session_id)
    total = query.count()
    records = query.order_by(MessageRow.created_at.desc()).offset(offset).limit(safe_limit).all()

    items = []
    for r in reversed(records):
        items.append({
            "id": r.id,
            "session_id": r.chat_session_id,
            "sender": r.sender,
            "content": r.content,
            "ml_severity": r.ml_severity,
            "llm_severity": r.llm_severity,
            "suggestions": json.loads(r.suggestions) if r.suggestions else [],
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return {"messages": items, "count": len(items), "total": total}


@chat_router.post("/chat/messages/{message_id}/feedback")
def submit_message_feedback(
    message_id: int,
    request: Dict[str, Any],
    http_request: Request,
    db: Session = Depends(get_db),
):
    """Record student feedback (+1 helpful, -1 unhelpful, optional comment) on AI response."""
    user = _get_optional_user(http_request, db)
    message = db.query(MessageRow).filter(MessageRow.id == message_id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")

    rating = request.get("rating")
    if rating not in (1, -1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be 1 or -1.")

    from database import MessageFeedbackRow
    feedback = MessageFeedbackRow(
        message_id=message_id,
        user_id=user.id if user else None,
        rating=rating,
        comment=str(request.get("comment", "")).strip()[:500] if request.get("comment") else None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(feedback)
    db.commit()
    return {"success": True, "message": "Feedback recorded. Thank you for helping Zenith improve."}


@chat_router.post("/chat/messages/{message_id}/regenerate", response_model=ChatResponse)
async def regenerate_message(
    message_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
):
    """Regenerate the AI response for the message preceding message_id."""
    user = _get_optional_user(http_request, db)
    message = db.query(MessageRow).filter(MessageRow.id == message_id).first()
    if not message or message.sender != "assistant":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assistant message not found.")

    chat_session = db.query(ChatSessionRow).filter(ChatSessionRow.session_id == message.chat_session_id).first()
    if not chat_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    if chat_session.user_id is not None:
        if not user or user.id != chat_session.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    # Find the preceding user prompt
    prev_user_msg = (
        db.query(MessageRow)
        .filter(
            MessageRow.chat_session_id == message.chat_session_id,
            MessageRow.sender == "user",
            MessageRow.created_at <= message.created_at,
        )
        .order_by(MessageRow.created_at.desc())
        .first()
    )
    prompt_text = prev_user_msg.content if prev_user_msg else (chat_session.request_message or "Hello")

    is_crisis = detect_deterministic_crisis(prompt_text)
    history = _build_conversation_history(db, message.chat_session_id)

    ai_payload = await generate_ai_chat_async(prompt_text, history=history, is_crisis=is_crisis)
    final_severity = "crisis" if is_crisis else ai_payload.get("severity", "low")

    # Update assistant message
    message.content = ai_payload["text"]
    message.llm_severity = final_severity
    message.suggestions = json.dumps(ai_payload["suggestions"])
    chat_session.response_text = ai_payload["text"]
    chat_session.severity = final_severity

    db.commit()
    db.refresh(message)

    return ChatResponse(
        id=str(message.id),
        text=message.content,
        severity=final_severity,
        suggestions=ai_payload["suggestions"],
        session_id=message.chat_session_id,
        ml_severity=message.ml_severity,
        ml_confidence=message.ml_confidence,
        created_at=message.created_at,
    )
