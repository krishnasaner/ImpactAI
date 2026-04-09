"""
ImpactAI — Authentication routes (signup / login / me / google).

All user data is stored in the local SQLite database.
JWT tokens are set as HTTP‑only cookies **and** returned in the
JSON body so the frontend can use either approach.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    JWT_EXPIRATION_HOURS,
)
from database import get_db, UserRow
from schemas import AuthResponse, LoginRequest, SignupRequest, UserResponse
from services.security import (
    create_access_token,
    decode_access_token,
    extract_token,
    hash_password,
    verify_password,
)

auth_router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_user_response(user: UserRow) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role or "student",
        name=user.name,
    )


def _set_token_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,  # set True in production behind HTTPS
        samesite="lax",
        max_age=int(timedelta(hours=JWT_EXPIRATION_HOURS).total_seconds()),
    )


# ── Signup ─────────────────────────────────────────────────────────────────────

@auth_router.post("/signup", response_model=AuthResponse)
def signup(
    request: SignupRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    normalized_email = request.email.lower().strip()

    existing = db.query(UserRow).filter(UserRow.email == normalized_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )

    hashed = hash_password(request.password)
    user = UserRow(
        email=normalized_email,
        hashed_password=hashed,
        role=request.role,
        name=request.name or normalized_email.split("@", 1)[0],
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({
        "sub": str(user.id),
        "email": normalized_email,
        "role": request.role,
    })
    _set_token_cookie(response, token)

    return {"user": _build_user_response(user), "token": token}


# ── Login ──────────────────────────────────────────────────────────────────────

@auth_router.post("/login", response_model=AuthResponse)
def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    normalized_email = request.email.lower().strip()
    user = db.query(UserRow).filter(UserRow.email == normalized_email).first()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token({
        "sub": str(user.id),
        "email": normalized_email,
        "role": user.role or "student",
    })
    _set_token_cookie(response, token)

    return {"user": _build_user_response(user), "token": token}


# ── Current User ───────────────────────────────────────────────────────────────

def _resolve_current_user(request: Request, db: Session) -> UserRow:
    """Extract + verify token → return the UserRow or raise 401."""
    token = extract_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
        )
    try:
        payload = decode_access_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    user = db.query(UserRow).filter(UserRow.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )
    return user


@auth_router.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    user = _resolve_current_user(request, db)
    return {"user": _build_user_response(user)}


# ── Logout ─────────────────────────────────────────────────────────────────────

@auth_router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully."}


# ── Google OAuth (stub — remains for frontend compatibility) ───────────────────

@auth_router.get("/google")
def google_oauth(role: Optional[str] = "student"):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return HTMLResponse(
            content=(
                "<h1>Google OAuth is not configured.</h1>"
                "<p>Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in Backend/.env</p>"
            ),
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
        )
    query = (
        f"response_type=code&client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20email%20profile&"
        f"state={role}"
    )
    return RedirectResponse(
        f"https://accounts.google.com/o/oauth2/v2/auth?{query}"
    )
