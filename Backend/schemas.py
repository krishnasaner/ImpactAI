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


# ── User Profile & Preferences ────────────────────────────────────────────────

class UserProfileRequest(BaseModel):
    display_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    university: Optional[str] = None
    major: Optional[str] = None
    student_id: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    license: Optional[str] = None
    experience: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: int
    user_id: int
    email: EmailStr
    role: str
    name: Optional[str] = None
    display_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    university: Optional[str] = None
    major: Optional[str] = None
    student_id: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    license: Optional[str] = None
    experience: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserPreferencesRequest(BaseModel):
    preferred_language: Optional[str] = "en"
    theme: Optional[str] = "system"
    email_notifications: Optional[bool] = True
    push_notifications: Optional[bool] = True
    mood_reminders: Optional[bool] = True
    journal_reminders: Optional[bool] = True
    anonymous_mode: Optional[bool] = False
    data_sharing_consent: Optional[bool] = False


class UserPreferencesResponse(BaseModel):
    user_id: int
    preferred_language: str
    theme: str
    email_notifications: bool
    push_notifications: bool
    mood_reminders: bool
    journal_reminders: bool
    anonymous_mode: bool
    data_sharing_consent: bool


# ── Journaling ────────────────────────────────────────────────────────────────

class JournalCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    mood_score: Optional[int] = Field(None, ge=1, le=5)
    tags: Optional[List[str]] = Field(default_factory=list)
    is_pinned: Optional[bool] = False


class JournalUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    mood_score: Optional[int] = Field(None, ge=1, le=5)
    tags: Optional[List[str]] = None
    is_pinned: Optional[bool] = None


class JournalResponse(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    mood_score: Optional[int] = None
    tags: List[str] = []
    is_pinned: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


# ── Wellness Plans & Activities ───────────────────────────────────────────────

class WellnessActivityCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    frequency: Optional[str] = "daily"


class WellnessActivityUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    completed: Optional[bool] = None


class WellnessActivityResponse(BaseModel):
    id: int
    plan_id: int
    title: str
    description: Optional[str] = None
    frequency: str
    progress: int
    completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime


class WellnessPlanCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[Literal["wellness", "academic", "social", "personal"]] = "wellness"
    target_date: Optional[datetime] = None
    activities: Optional[List[WellnessActivityCreateRequest]] = Field(default_factory=list)


class WellnessPlanUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[Literal["active", "paused", "completed"]] = None
    target_date: Optional[datetime] = None


class WellnessPlanResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    category: str
    status: str
    target_date: Optional[datetime] = None
    activities: List[WellnessActivityResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None


# ── Resources & Bookmarks ─────────────────────────────────────────────────────

class ResourceResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    content_type: str
    read_time: str
    language: str
    content_url: Optional[str] = None
    content_body: Optional[str] = None
    tags: List[str] = []
    view_count: int = 0
    is_bookmarked: bool = False
    created_at: datetime


class ResourceCreateRequest(BaseModel):
    title: str
    description: str
    category: str
    content_type: Optional[str] = "article"
    read_time: Optional[str] = "5 min"
    language: Optional[str] = "en"
    content_url: Optional[str] = None
    content_body: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)


# ── Counsellors & Appointments ────────────────────────────────────────────────

class CounsellorResponse(BaseModel):
    id: int
    user_id: int
    name: str
    title: str
    specialties: List[str]
    languages: List[str]
    bio: Optional[str] = None
    rating: float
    review_count: int
    experience: str
    is_available: bool
    availability_slots: dict = {}


class AppointmentCreateRequest(BaseModel):
    counsellor_id: int
    appointment_date: datetime
    duration_minutes: Optional[int] = 45
    meeting_type: Optional[Literal["video", "audio", "in_person"]] = "video"
    notes: Optional[str] = None


class AppointmentUpdateRequest(BaseModel):
    status: Optional[Literal["scheduled", "completed", "cancelled", "pending"]] = None
    counsellor_notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: int
    student_id: int
    counsellor_id: int
    counsellor_name: Optional[str] = None
    student_name: Optional[str] = None
    appointment_date: datetime
    duration_minutes: int
    status: str
    meeting_type: str
    notes: Optional[str] = None
    created_at: datetime


# ── Notifications ─────────────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: str
    link: Optional[str] = None
    is_read: bool
    created_at: datetime


# ── Chat Enhancements ─────────────────────────────────────────────────────────

class ChatSessionRenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)


class MessageFeedbackRequest(BaseModel):
    rating: Literal[1, -1]
    comment: Optional[str] = None


class AdvancedChatOutput(BaseModel):
    reply: str
    severity: Literal["low", "medium", "high", "crisis"] = "low"
    emotion: Optional[str] = "neutral"
    intent: Optional[str] = "general_wellness"
    suggestions: List[str] = Field(default_factory=list)
    requires_followup: bool = False
    safety_action: Optional[str] = None
