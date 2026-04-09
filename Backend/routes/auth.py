"""
ImpactAI authentication routes.

Supports email/password auth plus Google OAuth when credentials are configured.
JWT tokens are returned in the response body and also set as HTTP-only cookies.
"""

from datetime import datetime, timedelta, timezone
import json
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from config import (
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    FRONTEND_URL,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    JWT_EXPIRATION_HOURS,
)
from database import UserRow, get_db
from schemas import AuthResponse, LoginRequest, SignupRequest, UserResponse
from services.security import (
    create_access_token,
    decode_access_token,
    extract_token,
    hash_password,
    verify_password,
)

auth_router = APIRouter()


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
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=int(timedelta(hours=JWT_EXPIRATION_HOURS).total_seconds()),
    )


def _frontend_auth_redirect(next_page: Optional[str], **params: str) -> str:
    destination = "signup" if next_page == "signup" else "login"
    query = urlencode({key: value for key, value in params.items() if value is not None})
    base = f"{FRONTEND_URL.rstrip('/')}/{destination}"
    return f"{base}?{query}" if query else base


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

    token = create_access_token(
        {
            "sub": str(user.id),
            "email": normalized_email,
            "role": request.role,
        }
    )
    _set_token_cookie(response, token)

    return {"user": _build_user_response(user), "token": token}


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

    token = create_access_token(
        {
            "sub": str(user.id),
            "email": normalized_email,
            "role": user.role or "student",
        }
    )
    _set_token_cookie(response, token)

    return {"user": _build_user_response(user), "token": token}


def _resolve_current_user(request: Request, db: Session) -> UserRow:
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


@auth_router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully."}


@auth_router.get("/google/status")
def google_oauth_status():
    return {
        "configured": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        "redirect_uri": GOOGLE_REDIRECT_URI,
    }


@auth_router.get("/google")
def google_oauth(role: Optional[str] = "student", next: Optional[str] = "login"):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return RedirectResponse(
            _frontend_auth_redirect(
                next,
                error="Google OAuth is not configured on the server.",
            ),
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    state = json.dumps(
        {
            "role": role or "student",
            "next": next or "login",
        }
    )
    query = urlencode(
        {
            "response_type": "code",
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "scope": "openid email profile",
            "state": state,
            "access_type": "online",
            "prompt": "select_account",
        }
    )
    return RedirectResponse(
        f"https://accounts.google.com/o/oauth2/v2/auth?{query}"
    )


@auth_router.get("/google/callback")
def google_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
):
    next_page = "login"
    role = "student"

    if state:
        try:
            state_data = json.loads(state)
            role = state_data.get("role", "student")
            next_page = state_data.get("next", "login")
        except json.JSONDecodeError:
            pass

    if error or not code:
        return RedirectResponse(
            _frontend_auth_redirect(
                next_page,
                error=error or "Google login was cancelled.",
            ),
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return RedirectResponse(
            _frontend_auth_redirect(
                next_page,
                error="Google OAuth is not configured on the server.",
            ),
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    try:
        token_response = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            timeout=15.0,
        )
        token_response.raise_for_status()
        token_data = token_response.json()

        userinfo_response = httpx.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
            timeout=15.0,
        )
        userinfo_response.raise_for_status()
        profile = userinfo_response.json()
    except Exception:
        return RedirectResponse(
            _frontend_auth_redirect(
                next_page,
                error="Google sign-in failed. Please try again.",
            ),
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    email = (profile.get("email") or "").lower().strip()
    if not email:
        return RedirectResponse(
            _frontend_auth_redirect(
                next_page,
                error="Google account did not provide an email address.",
            ),
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    user = db.query(UserRow).filter(UserRow.email == email).first()
    if not user:
        user = UserRow(
            email=email,
            hashed_password=hash_password(profile.get("sub", email)),
            role=role,
            name=profile.get("name") or email.split("@", 1)[0],
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role or "student",
        }
    )

    redirect_response = RedirectResponse(
        _frontend_auth_redirect(
            next_page,
            id=str(user.id),
            name=user.name or "",
            email=user.email,
            role=user.role or "student",
            token=token,
        ),
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
    _set_token_cookie(redirect_response, token)
    return redirect_response
