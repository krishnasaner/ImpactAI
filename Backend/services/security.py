"""
ImpactAI — Security utilities: password hashing, JWT tokens, and password policies.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import re

from jose import jwt, JWTError
from fastapi import Request
import bcrypt

from config import JWT_SECRET, JWT_ALGORITHM

# Dummy hash for timing attack protection on non-existent users
DUMMY_HASH = b"$2b$10$eA3aGj/P5ZJ6fK7n5GfJJuHw7C8sH4sB2eD9xR4b3y2o2s2e2e2e2"
COMMON_WEAK_PASSWORDS = {"123", "password", "123456", "qwerty", "abc123"}

# ── Password Policy & Hashing ──────────────────────────────────────────────────

def hash_password(password: str) -> str:
    # Truncate to 72 bytes to satisfy bcrypt requirements
    pwd_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt(rounds=10)).decode("utf-8")


def verify_password_with_timing_defense(plain_password: str, hashed_password: Optional[str]) -> bool:
    """
    Verify password. If the user doesn't exist, execute a dummy check
    to mitigate timing attacks.
    """
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        if not hashed_password:
            # Perform dummy verification to consume time
            bcrypt.checkpw(pwd_bytes, DUMMY_HASH)
            return False
        
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Enforce password policy:
    - Reject common weak passwords
    - Minimum 12 characters
    - Must contain uppercase, lowercase, numbers, and special characters
    """
    if password in COMMON_WEAK_PASSWORDS:
        return False, "Password is too common and insecure."
    
    if len(password) < 12:
        return False, "Password must be at least 12 characters long."
        
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
        
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
        
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
        
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
        
    return True, ""


# ── JWT helpers ────────────────────────────────────────────────────────────────

def create_access_token(data: dict) -> str:
    """Access token expires in 15 minutes."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta) -> str:
    """Refresh token has configurable expiration (e.g. 7 or 30 days)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str, expected_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != expected_type:
            raise ValueError(f"Invalid token type: expected {expected_type}")
        return payload
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc


def extract_token(request: Request) -> Optional[str]:
    """Extract Bearer token from Authorization header or cookie."""
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ", 1)[1]
    return request.cookies.get("access_token")
