"""Security utilities for authentication, CSRF protection, and OAuth state."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import re
import secrets

import bcrypt
from fastapi import Request
from jose import JWTError, jwt

from config import (
    ACCESS_COOKIE_NAME,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    GOOGLE_OAUTH_STATE_TTL_SECONDS,
    JWT_ALGORITHM,
    JWT_SECRET,
)

DUMMY_HASH = b"$2b$10$N9qo8uLOickgx2ZMRZo5i.ej8E6B7d3n0Q7Yx8qM9Kf6J5M2Aq4wK"
COMMON_WEAK_PASSWORDS = {
    "123",
    "123456",
    "123456789",
    "1234567890",
    "abc123",
    "admin123",
    "impactai123",
    "letmein",
    "password",
    "password123",
    "qwerty",
    "welcome123",
}
_ALLOWED_REDIRECT_TARGETS = {"login", "signup"}


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password_with_timing_defense(
    plain_password: str,
    hashed_password: Optional[str],
) -> bool:
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        if not hashed_password:
            bcrypt.checkpw(pwd_bytes, DUMMY_HASH)
            return False
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False


def validate_password_strength(password: str) -> Tuple[bool, str]:
    normalized = password.strip()
    if normalized.lower() in COMMON_WEAK_PASSWORDS:
        return False, "Password is too common and insecure."
    if len(normalized) < 12:
        return False, "Password must be at least 12 characters long."
    if not re.search(r"[A-Z]", normalized):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", normalized):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", normalized):
        return False, "Password must contain at least one number."
    if not re.search(r"[^A-Za-z0-9]", normalized):
        return False, "Password must contain at least one special character."
    if normalized.lower().startswith("password") or normalized.lower().startswith("impactai"):
        return False, "Password is too predictable. Choose a more unique password."
    return True, ""


def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    now = datetime.now(timezone.utc)
    to_encode = data.copy()
    to_encode.update(
        {
            "exp": now + timedelta(minutes=expires_minutes),
            "iat": now,
            "jti": secrets.token_urlsafe(16),
            "type": "access",
        }
    )
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    to_encode = data.copy()
    to_encode.update(
        {
            "exp": now + expires_delta,
            "iat": now,
            "jti": secrets.token_urlsafe(24),
            "type": "refresh",
        }
    )
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str, expected_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != expected_type:
            raise ValueError(f"Invalid token type: expected {expected_type}")
        return payload
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc


def issue_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def validate_csrf(request: Request) -> None:
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get(CSRF_HEADER_NAME)
    if not cookie_token or not header_token:
        raise ValueError("CSRF validation failed.")
    if not secrets.compare_digest(cookie_token, header_token):
        raise ValueError("CSRF validation failed.")


def create_oauth_state(role: str, next_target: str) -> str:
    now = datetime.now(timezone.utc)
    safe_next = next_target if next_target in _ALLOWED_REDIRECT_TARGETS else "login"
    safe_role = role if role in {"student", "counselor", "admin"} else "student"
    payload = {
        "role": safe_role,
        "next": safe_next,
        "nonce": secrets.token_urlsafe(12),
        "type": "oauth_state",
        "iat": now,
        "exp": now + timedelta(seconds=GOOGLE_OAUTH_STATE_TTL_SECONDS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_oauth_state(state: str) -> dict:
    try:
        payload = jwt.decode(state, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid OAuth state") from exc
    if payload.get("type") != "oauth_state":
        raise ValueError("Invalid OAuth state")
    payload["role"] = payload.get("role") if payload.get("role") in {"student", "counselor", "admin"} else "student"
    payload["next"] = payload.get("next") if payload.get("next") in _ALLOWED_REDIRECT_TARGETS else "login"
    return payload


def extract_token(request: Request) -> Optional[str]:
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ", 1)[1]
    return request.cookies.get(ACCESS_COOKIE_NAME)
