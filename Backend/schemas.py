from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    role: Literal["student", "counselor", "admin"]
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: Literal["student", "counselor", "admin"]


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: str
    name: Optional[str] = None


class AuthResponse(BaseModel):
    user: UserResponse
    token: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    id: str
    text: str
    severity: Literal["low", "medium", "high", "crisis"]
    suggestions: List[str]
    session_id: str
    created_at: datetime


class AnalyticsSummary(BaseModel):
    row_count: int
    average_context_tokens: float
    average_response_tokens: float
    context_length_distribution: dict
    response_length_distribution: dict
