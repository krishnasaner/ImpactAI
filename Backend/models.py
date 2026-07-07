"""
ImpactAI — Pydantic domain models for internal use.

These represent the canonical shape of domain objects after they
have been read from / before they are written to the database.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr


class UserInDB(BaseModel):
    id: int
    email: EmailStr
    hashed_password: str
    role: str
    name: Optional[str] = None
    created_at: datetime
    is_verified: int = 0
    failed_login_attempts: int = 0
    lockout_until: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatRecord(BaseModel):
    id: int
    session_id: str
    user_id: Optional[int] = None
    user_role: str = "anonymous"
    request_message: Optional[str] = None
    response_text: Optional[str] = None
    severity: str = "low"
    suggestions: List[str] = []
    ml_severity: Optional[str] = None
    ml_confidence: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageRecord(BaseModel):
    id: int
    chat_session_id: str
    sender: str
    content: str
    ml_severity: Optional[str] = None
    ml_confidence: Optional[float] = None
    llm_severity: Optional[str] = None
    suggestions: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class MoodEntry(BaseModel):
    id: int
    user_id: Optional[int] = None
    mood: str
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
