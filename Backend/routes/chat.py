from datetime import datetime
from uuid import uuid4
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status

from database import chat_collection
from routes.auth import _resolve_current_user
from schemas import ChatRequest, ChatResponse
from services.openai_client import generate_ai_chat

chat_router = APIRouter()


def _get_optional_user(request: Request) -> Optional[dict]:
    try:
        return _resolve_current_user(request)
    except HTTPException:
        return None


@chat_router.post("/chat", response_model=ChatResponse)
async def create_chat(request: ChatRequest, http_request: Request):
    user_doc = _get_optional_user(http_request)
    if not request.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message text cannot be empty.")

    ai_payload = generate_ai_chat(request.message)
    session_id = request.session_id or str(uuid4())
    chat_record = {
        "session_id": session_id,
        "user_id": str(user_doc["_id"]) if user_doc else None,
        "user_role": user_doc.get("role") if user_doc else "anonymous",
        "request_message": request.message,
        "response_text": ai_payload["text"],
        "severity": ai_payload["severity"],
        "suggestions": ai_payload["suggestions"],
        "created_at": datetime.utcnow(),
    }
    chat_collection.insert_one(chat_record)

    return ChatResponse(
        id=str(uuid4()),
        text=ai_payload["text"],
        severity=ai_payload["severity"],
        suggestions=ai_payload["suggestions"],
        session_id=session_id,
        created_at=datetime.utcnow(),
    )
