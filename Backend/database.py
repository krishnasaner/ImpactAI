"""
ImpactAI — SQLite database layer using SQLAlchemy ORM.

Data is stored locally at  Backend/data/impactai.db
No external database server (Mongo / Postgres) is required.
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, event
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime, timezone

from config import DATABASE_PATH

# ── Ensure the data directory exists ───────────────────────────────────────────
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite + FastAPI
    echo=False,
)

# Enable WAL mode for better concurrent read performance
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ═══════════════════════════════ ORM Models ═══════════════════════════════════

class UserRow(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="student")
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ChatSessionRow(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    user_role = Column(String(50), default="anonymous")
    request_message = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    severity = Column(String(20), default="low")
    suggestions = Column(Text, default="[]")  # JSON‑encoded list
    ml_severity = Column(String(20), nullable=True)  # ML model prediction
    ml_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class MoodEntryRow(Base):
    __tablename__ = "mood_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True, index=True)
    mood = Column(String(50), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ═══════════════════════════ Lifecycle helpers ════════════════════════════════

def init_db() -> None:
    """Create all tables if they don't exist yet."""
    Base.metadata.create_all(bind=engine)
    print(f"[DB] SQLite database ready at {DATABASE_PATH}")


def get_db():
    """FastAPI dependency — yields a scoped session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
