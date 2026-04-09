"""
ImpactAI — Pydantic domain models for internal use.

These are *not* the request/response schemas (see schemas.py).
They represent the canonical shape of domain objects after they
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

    class Config:
        from_attributes = True


class ChatRecord(BaseModel):
    id: int
    session_id: str
    user_id: Optional[int] = None
    user_role: str = "anonymous"
    request_message: str
    response_text: str
    severity: str = "low"
    suggestions: List[str] = []
    ml_severity: Optional[str] = None
    ml_confidence: Optional[float] = None
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
