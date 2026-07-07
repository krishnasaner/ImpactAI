"""
ImpactAI authentication routes.

Supports email/password auth plus Google OAuth when credentials are configured.
JWT access and refresh tokens are managed via secure HttpOnly cookies.
"""

from datetime import datetime, timedelta, timezone
import json
import hashlib
from uuid import uuid4
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
)
from database import UserRow, SessionRow, RefreshTokenRow, get_db
from schemas import AuthResponse, LoginRequest, SignupRequest, UserResponse, ApiResponse
from services.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    extract_token,
    hash_password,
    verify_password_with_timing_defense,
    validate_password_strength,
)
from services.logging import log_audit_event, log_security_event

auth_router = APIRouter()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _build_user_response(user: UserRow) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role or "student",
        name=user.name,
    )


def _set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    remember_me: bool,
) -> None:
    # Set access token cookie (always short-lived session context, max_age 15 mins)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=900,  # 15 minutes
        path="/",
    )

    # Set refresh token cookie (session-lifetime or persistent)
    refresh_max_age = int(timedelta(days=30 if remember_me else 7).total_seconds())
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=refresh_max_age if remember_me else None,  # None means expires on browser close
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


def _get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return ip, ua


def _create_user_session(
    db: Session,
    user: UserRow,
    remember_me: bool,
    ip_address: Optional[str],
    user_agent: Optional[str],
) -> tuple[str, str, str]:
    """
    Creates a user session and a refresh token row in database,
    returning (access_token, refresh_token, session_id).
    """
    session_id = str(uuid4())
    refresh_expiry = timedelta(days=30 if remember_me else 7)
    expires_at = datetime.now(timezone.utc) + refresh_expiry

    # Register active session record
    db_session = SessionRow(
        user_id=user.id,
        session_id=session_id,
        user_agent=user_agent,
        ip_address=ip_address,
        last_activity=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        expires_at=expires_at,
        is_active=1,
    )
    db.add(db_session)
    db.commit()

    # Generate tokens
    access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role or "student",
        }
    )
    refresh_token = create_refresh_token(
        {
            "sub": str(user.id),
            "session_id": session_id,
        },
        expires_delta=refresh_expiry,
    )

    # Register refresh token
    token_hash = _hash_token(refresh_token)
    db_refresh = RefreshTokenRow(
        user_id=user.id,
        session_id=session_id,
        token_hash=token_hash,
        created_at=datetime.now(timezone.utc),
        expires_at=expires_at,
        is_revoked=0,
    )
    db.add(db_refresh)
    db.commit()

    return access_token, refresh_token, session_id


@auth_router.post("/signup", response_model=AuthResponse)
def signup(
    request: SignupRequest,
    http_request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    ip, ua = _get_client_info(http_request)
    normalized_email = request.email.lower().strip()

    # 1. Validation
    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match.",
        )

    ok, error_msg = validate_password_strength(request.password)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    existing = db.query(UserRow).filter(UserRow.email == normalized_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )

    # 2. Hashing and registration
    hashed = hash_password(request.password)
    user = UserRow(
        email=normalized_email,
        hashed_password=hashed,
        role=request.role,
        name=request.name or normalized_email.split("@", 1)[0],
        created_at=datetime.now(timezone.utc),
        is_verified=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 3. Establish Session & Tokens
    access_token, refresh_token, _ = _create_user_session(
        db, user, request.remember_me, ip, ua
    )
    _set_auth_cookies(response, access_token, refresh_token, request.remember_me)

    log_audit_event(
        db,
        "SIGNUP",
        f"User signed up: {normalized_email}",
        user.id,
        ip,
        ua,
    )

    return {
        "success": True,
        "message": "Signup successful.",
        "user": _build_user_response(user),
        "token": access_token,
        "data": {"user": _build_user_response(user)},
    }


@auth_router.post("/login", response_model=AuthResponse)
def login(
    request: LoginRequest,
    http_request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    ip, ua = _get_client_info(http_request)
    normalized_email = request.email.lower().strip()
    user = db.query(UserRow).filter(UserRow.email == normalized_email).first()

    # Generic error message to prevent account enumeration attacks
    generic_error = "Invalid email or password."

    if not user:
        # Dummy validation execution to consume identical time (mitigate timing attacks)
        verify_password_with_timing_defense(request.password, None)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=generic_error,
        )

    # Check brute-force lockout status
    if user.lockout_until and user.lockout_until > datetime.now(timezone.utc):
        log_security_event(
            db,
            "BRUTE_FORCE",
            "high",
            f"Blocked login attempt on locked out user: {normalized_email}",
            user.id,
            ip,
            ua,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is temporarily locked due to multiple failed login attempts. Please try again in 15 minutes.",
        )

    # Verify credentials
    if not verify_password_with_timing_defense(request.password, user.hashed_password):
        # Increment failed login attempts
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.lockout_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            log_audit_event(
                db,
                "LOCKOUT",
                f"User account locked for 15m: {normalized_email}",
                user.id,
                ip,
                ua,
            )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=generic_error,
        )

    # Reset failed login count and log active details
    user.failed_login_attempts = 0
    user.lockout_until = None
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    # Create session and write HttpOnly cookies
    access_token, refresh_token, _ = _create_user_session(
        db, user, request.remember_me, ip, ua
    )
    _set_auth_cookies(response, access_token, refresh_token, request.remember_me)

    log_audit_event(
        db,
        "LOGIN",
        f"User logged in: {normalized_email}",
        user.id,
        ip,
        ua,
    )

    return {
        "success": True,
        "message": "Login successful.",
        "user": _build_user_response(user),
        "token": access_token,
        "data": {"user": _build_user_response(user)},
    }


def _resolve_current_user(request: Request, db: Session) -> UserRow:
    """Verifies access token directly from cookie or auth headers."""
    token = extract_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
        )

    try:
        payload = decode_token(token, "access")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
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
    return {
        "success": True,
        "message": "Current session loaded.",
        "user": _build_user_response(user),
        "data": {"user": _build_user_response(user)},
    }


@auth_router.post("/refresh")
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    ip, ua = _get_client_info(request)
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is missing.",
        )

    try:
        payload = decode_token(refresh_token, "refresh")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    user_id = payload.get("sub")
    session_id = payload.get("session_id")

    if not user_id or not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload.",
        )

    user = db.query(UserRow).filter(UserRow.id == int(user_id)).first()
    db_session = db.query(SessionRow).filter(SessionRow.session_id == session_id).first()

    # Replay attack protection: check if refresh token hash was already revoked
    token_hash = _hash_token(refresh_token)
    db_token = db.query(RefreshTokenRow).filter(RefreshTokenRow.token_hash == token_hash).first()

    if not user or not db_session or not db_session.is_active or not db_token:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Active session not found.",
        )

    if db_token.is_revoked:
        # Revoke ALL active sessions/tokens for user immediately as this is a replay attack!
        db.query(SessionRow).filter(SessionRow.user_id == user.id).update({"is_active": 0})
        db.query(RefreshTokenRow).filter(RefreshTokenRow.user_id == user.id).update({"is_revoked": 1})
        db.commit()

        _clear_auth_cookies(response)
        log_security_event(
            db,
            "JWT_REPLAY",
            "critical",
            f"Token replay attack detected! Revoked all sessions for user {user.email}.",
            user.id,
            ip,
            ua,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked due to security violation.",
        )

    # Set old token as revoked
    db_token.is_revoked = 1
    db.commit()

    # Update last activity
    db_session.last_activity = datetime.now(timezone.utc)

    # Determine remember me based on expiration window
    remember_me = (db_session.expires_at - datetime.now(timezone.utc)) > timedelta(days=8)
    refresh_expiry = timedelta(days=30 if remember_me else 7)

    # Generate new rotated tokens
    new_access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role or "student",
        }
    )
    new_refresh_token = create_refresh_token(
        {
            "sub": str(user.id),
            "session_id": session_id,
        },
        expires_delta=refresh_expiry,
    )

    # Write new refresh token record
    new_token_hash = _hash_token(new_refresh_token)
    db_new_token = RefreshTokenRow(
        user_id=user.id,
        session_id=session_id,
        token_hash=new_token_hash,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + refresh_expiry,
        is_revoked=0,
    )
    db.add(db_new_token)
    db.commit()

    _set_auth_cookies(response, new_access_token, new_refresh_token, remember_me)

    return {
        "success": True,
        "message": "Token refreshed successfully.",
        "token": new_access_token,
    }


@auth_router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    ip, ua = _get_client_info(request)
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        try:
            payload = decode_token(refresh_token, "refresh")
            session_id = payload.get("session_id")
            if session_id:
                # Mark session inactive
                db.query(SessionRow).filter(SessionRow.session_id == session_id).update({"is_active": 0})
                # Revoke refresh token
                token_hash = _hash_token(refresh_token)
                db.query(RefreshTokenRow).filter(RefreshTokenRow.token_hash == token_hash).update({"is_revoked": 1})
                db.commit()

                user_id = int(payload.get("sub", 0))
                if user_id:
                    log_audit_event(db, "LOGOUT", "User logged out current session.", user_id, ip, ua)
        except Exception:
            pass

    _clear_auth_cookies(response)
    return {"success": True, "message": "Logged out successfully."}


@auth_router.post("/logout/all")
def logout_all_devices(request: Request, response: Response, db: Session = Depends(get_db)):
    ip, ua = _get_client_info(request)
    user = _resolve_current_user(request, db)

    # Revoke all sessions
    db.query(SessionRow).filter(SessionRow.user_id == user.id).update({"is_active": 0})
    db.query(RefreshTokenRow).filter(RefreshTokenRow.user_id == user.id).update({"is_revoked": 1})
    db.commit()

    _clear_auth_cookies(response)
    log_audit_event(db, "LOGOUT_ALL", "User logged out all devices.", user.id, ip, ua)

    return {"success": True, "message": "Logged out from all devices successfully."}


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
            f"{FRONTEND_URL.rstrip('/')}/{next}?error=Google OAuth is not configured on the-server",
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
    request: Request,
    response: Response,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
):
    ip, ua = _get_client_info(request)
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
        err_msg = error or "Google login was cancelled."
        return RedirectResponse(f"{FRONTEND_URL.rstrip('/')}/{next_page}?error={err_msg}")

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return RedirectResponse(f"{FRONTEND_URL.rstrip('/')}/{next_page}?error=Google configuration error.")

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
        return RedirectResponse(f"{FRONTEND_URL.rstrip('/')}/{next_page}?error=Google server communications failed")

    email = (profile.get("email") or "").lower().strip()
    if not email:
        return RedirectResponse(f"{FRONTEND_URL.rstrip('/')}/{next_page}?error=Google email not provided")

    user = db.query(UserRow).filter(UserRow.email == email).first()
    is_new = False
    if not user:
        is_new = True
        user = UserRow(
            email=email,
            # Placeholder hashed password since OAuth users don't use passwords
            hashed_password=hash_password(str(uuid4())),
            role=role,
            name=profile.get("name") or email.split("@", 1)[0],
            created_at=datetime.now(timezone.utc),
            is_verified=1,  # Google-verified email address
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Establish secure session and set HttpOnly cookies
    access_token, refresh_token, _ = _create_user_session(db, user, True, ip, ua)
    
    # We construct a redirect response and write cookies directly to it!
    # No tokens are exposed in the redirection URL.
    dashboard_route = "/app/admin-dashboard" if user.role in ("admin", "counselor") else "/app/student-dashboard"
    redirect_url = f"{FRONTEND_URL.rstrip('/')}{dashboard_route}"
    
    redirect_response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    _set_auth_cookies(redirect_response, access_token, refresh_token, True)

    log_audit_event(
        db,
        "SIGNUP" if is_new else "LOGIN",
        f"Google Authentication: {user.email}",
        user.id,
        ip,
        ua,
    )

    return redirect_response
