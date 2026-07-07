"""
ImpactAI — Request / Response schemas (Pydantic v2).

These are the shapes that the FastAPI routes accept and return.
"""

from datetime import datetime, timezone
from typing import List, Optional, Literal, Generic, TypeVar, Any
from pydantic import BaseModel, EmailStr, Field

T = TypeVar("T")

# ── Standardized Response Envelope ─────────────────────────────────────────────

class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = ""
    data: Optional[T] = None
    errors: List[str] = []
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Auth ───────────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str
    role: Literal["student", "counselor", "admin"] = "student"
    name: Optional[str] = None
    remember_me: Optional[bool] = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: Literal["student", "counselor", "admin"] = "student"
    remember_me: Optional[bool] = True


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    name: Optional[str] = None


class AuthResponse(ApiResponse[dict]):
    user: UserResponse
    token: Optional[str] = None


# ── Chat ───────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    id: str
    text: str
    severity: Literal["low", "medium", "high", "crisis"]
    suggestions: List[str]
    session_id: str
    ml_severity: Optional[str] = None
    ml_confidence: Optional[float] = None
    created_at: datetime


# ── Analytics ──────────────────────────────────────────────────────────────────

class AnalyticsSummary(BaseModel):
    row_count: int
    average_context_tokens: float
    average_response_tokens: float
    context_length_distribution: dict
    response_length_distribution: dict


# ── Mood ───────────────────────────────────────────────────────────────────────

class MoodRequest(BaseModel):
    mood: str
    note: Optional[str] = None


class MoodResponse(BaseModel):
    id: int
    mood: str
    note: Optional[str] = None
    created_at: datetime


# ── ML ─────────────────────────────────────────────────────────────────────────

class SeverityPrediction(BaseModel):
    text: str
    predicted_severity: str
    confidence: float
