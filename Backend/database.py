"""
ImpactAI database layer using SQLAlchemy ORM.

Data is stored locally in SQLite by default, with a configurable path for
local development and automated verification.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, event, inspect
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_PATH

DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
    pool_pre_ping=True,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class UserRow(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="student")
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_verified = Column(Integer, default=0)
    verification_token = Column(String(64), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    lockout_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)


class SessionRow(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    last_activity = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Integer, default=1)
    remember_me = Column(Integer, nullable=False, default=1)


class RefreshTokenRow(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(64), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Integer, default=0)


class ChatSessionRow(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(100), default="New Conversation")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_role = Column(String(50), default="anonymous")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    request_message = Column(Text, nullable=True)
    response_text = Column(Text, nullable=True)
    severity = Column(String(20), default="low")
    suggestions = Column(Text, default="[]")
    ml_severity = Column(String(20), nullable=True)
    ml_confidence = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)


class MessageRow(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_session_id = Column(String(64), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    ml_severity = Column(String(20), nullable=True)
    ml_confidence = Column(Float, nullable=True)
    llm_severity = Column(String(20), nullable=True)
    suggestions = Column(Text, default="[]")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class MoodEntryRow(Base):
    __tablename__ = "mood_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    mood = Column(String(50), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLogRow(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SecurityLogRow(Base):
    __tablename__ = "security_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), default="medium")
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class UserProfileRow(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=True)
    phone = Column(String(30), nullable=True)
    date_of_birth = Column(String(30), nullable=True)
    university = Column(String(150), nullable=True)
    major = Column(String(100), nullable=True)
    student_id = Column(String(50), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)
    license = Column(String(100), nullable=True)
    experience = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class UserPreferencesRow(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    preferred_language = Column(String(10), default="en")
    theme = Column(String(20), default="system")
    email_notifications = Column(Integer, default=1)
    push_notifications = Column(Integer, default=1)
    mood_reminders = Column(Integer, default=1)
    journal_reminders = Column(Integer, default=1)
    anonymous_mode = Column(Integer, default=0)
    data_sharing_consent = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class JournalEntryRow(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    mood_score = Column(Integer, nullable=True)
    tags = Column(Text, default="[]")
    is_pinned = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class WellnessPlanRow(Base):
    __tablename__ = "wellness_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), default="wellness")
    status = Column(String(20), default="active")
    target_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class WellnessActivityRow(Base):
    __tablename__ = "wellness_activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("wellness_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    frequency = Column(String(50), default="daily")
    progress = Column(Integer, default=0)
    completed = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ResourceRow(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)
    content_type = Column(String(30), default="article")
    read_time = Column(String(30), default="5 min")
    language = Column(String(10), default="en")
    content_url = Column(Text, nullable=True)
    content_body = Column(Text, nullable=True)
    tags = Column(Text, default="[]")
    is_published = Column(Integer, default=1)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ResourceBookmarkRow(Base):
    __tablename__ = "resource_bookmarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CounsellorProfileRow(Base):
    __tablename__ = "counsellor_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    title = Column(String(100), default="Licensed Student Counselor")
    specialties = Column(Text, default="[]")
    languages = Column(Text, default='["en"]')
    bio = Column(Text, nullable=True)
    rating = Column(Float, default=4.9)
    review_count = Column(Integer, default=0)
    experience = Column(String(50), default="5+ years")
    is_available = Column(Integer, default=1)
    availability_slots = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AppointmentRow(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    counsellor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    appointment_date = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, default=45)
    status = Column(String(30), default="scheduled")
    meeting_type = Column(String(30), default="video")
    notes = Column(Text, nullable=True)
    counsellor_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class NotificationRow(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="reminder")
    link = Column(String(255), nullable=True)
    is_read = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class MessageFeedbackRow(Base):
    __tablename__ = "message_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def _ensure_columns() -> None:
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    with engine.begin() as connection:
        if "sessions" in table_names:
            columns = {column["name"] for column in inspector.get_columns("sessions")}
            if "remember_me" not in columns:
                connection.exec_driver_sql(
                    "ALTER TABLE sessions ADD COLUMN remember_me INTEGER NOT NULL DEFAULT 1"
                )

        if "chat_sessions" in table_names:
            chat_cols = {column["name"] for column in inspector.get_columns("chat_sessions")}
            if "title" not in chat_cols:
                connection.exec_driver_sql(
                    "ALTER TABLE chat_sessions ADD COLUMN title VARCHAR(100) DEFAULT 'New Conversation'"
                )
            if "summary" not in chat_cols:
                connection.exec_driver_sql(
                    "ALTER TABLE chat_sessions ADD COLUMN summary TEXT"
                )

        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_sessions_user_active ON sessions (user_id, is_active)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_sessions_expires_at ON sessions (expires_at)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_refresh_tokens_session_revoked ON refresh_tokens (session_id, is_revoked)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_revoked ON refresh_tokens (user_id, is_revoked)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_messages_session_created_at ON messages (chat_session_id, created_at)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_chat_sessions_user_created_at ON chat_sessions (user_id, created_at)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_mood_entries_user_created_at ON mood_entries (user_id, created_at)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_journal_entries_user ON journal_entries (user_id, created_at)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_wellness_plans_user ON wellness_plans (user_id, status)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_wellness_activities_plan ON wellness_activities (plan_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_resources_category ON resources (category, is_published)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_appointments_student ON appointments (student_id, appointment_date)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_appointments_counsellor ON appointments (counsellor_id, appointment_date)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_notifications_user ON notifications (user_id, is_read)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_audit_logs_user_created_at ON audit_logs (user_id, created_at)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_security_logs_user_created_at ON security_logs (user_id, created_at)"
        )


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_columns()
    print(f"[DB] SQLite database ready at {DATABASE_PATH}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
