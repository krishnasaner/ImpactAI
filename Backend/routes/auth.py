"""Authentication routes for ImpactAI."""

from datetime import datetime, timedelta, timezone
import hashlib
from typing import Optional
from urllib.parse import urlencode
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from config import (
    ACCESS_COOKIE_NAME,
    COOKIE_DOMAIN,
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    CSRF_COOKIE_NAME,
    FRONTEND_URL,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    REFRESH_COOKIE_NAME,
    REFRESH_TOKEN_EXPIRE_DAYS,
    REFRESH_TOKEN_REMEMBER_ME_DAYS,
    SESSION_ACTIVITY_UPDATE_SECONDS,
)
from database import RefreshTokenRow, SessionRow, UserRow, get_db
from schemas import AuthResponse, LoginRequest, SignupRequest, UserResponse
from services.logging import log_audit_event, log_security_event
from services.rate_limit import rate_limiter
from services.security import (
    create_access_token,
    create_oauth_state,
    create_refresh_token,
    decode_oauth_state,
    decode_token,
    extract_token,
    hash_password,
    issue_csrf_token,
    validate_password_strength,
    verify_password_with_timing_defense,
)

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


def _set_csrf_cookie(response: Response, csrf_token: str) -> None:
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
        domain=COOKIE_DOMAIN,
    )


def _set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    remember_me: bool,
    csrf_token: Optional[str] = None,
) -> None:
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=900,
        path="/",
        domain=COOKIE_DOMAIN,
    )

    refresh_max_age = int(
        timedelta(days=REFRESH_TOKEN_REMEMBER_ME_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS).total_seconds()
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=refresh_max_age if remember_me else None,
        path="/",
        domain=COOKIE_DOMAIN,
    )
    _set_csrf_cookie(response, csrf_token or issue_csrf_token())


def _clear_auth_cookies(response: Response) -> None:
    for cookie_name in (ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME, CSRF_COOKIE_NAME):
        response.delete_cookie(cookie_name, path="/", domain=COOKIE_DOMAIN)


def _get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    forwarded_for = request.headers.get("x-forwarded-for")
    ip = forwarded_for.split(",", 1)[0].strip() if forwarded_for else None
    if not ip and request.client:
        ip = request.client.host
    ua = request.headers.get("user-agent")
    return ip, ua


def _to_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _reject_if_rate_limited(scope: str, key: str, limit: int, window_seconds: int) -> None:
    retry_after = rate_limiter.check(scope, key, limit, window_seconds)
    if retry_after:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )


def _create_user_session(
    db: Session,
    user: UserRow,
    remember_me: bool,
    ip_address: Optional[str],
    user_agent: Optional[str],
) -> tuple[str, str, str]:
    session_id = str(uuid4())
    refresh_expiry = timedelta(
        days=REFRESH_TOKEN_REMEMBER_ME_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS
    )
    expires_at = datetime.now(timezone.utc) + refresh_expiry

    db_session = SessionRow(
        user_id=user.id,
        session_id=session_id,
        user_agent=user_agent,
        ip_address=ip_address,
        last_activity=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        expires_at=expires_at,
        is_active=1,
        remember_me=1 if remember_me else 0,
    )
    db.add(db_session)
    db.flush()

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role or "student",
            "session_id": session_id,
        }
    )
    refresh_token = create_refresh_token(
        {
            "sub": str(user.id),
            "session_id": session_id,
        },
        expires_delta=refresh_expiry,
    )

    db.add(
        RefreshTokenRow(
            user_id=user.id,
            session_id=session_id,
            token_hash=_hash_token(refresh_token),
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            is_revoked=0,
        )
    )
    db.commit()
    return access_token, refresh_token, session_id


def _resolve_current_user(request: Request, db: Session) -> UserRow:
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
    session_id = payload.get("session_id")
    if not user_id or not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    user = db.query(UserRow).filter(UserRow.id == int(user_id)).first()
    db_session = db.query(SessionRow).filter(SessionRow.session_id == session_id).first()
    if not user or not db_session or db_session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    now = datetime.now(timezone.utc)
    session_expires_at = _to_utc(db_session.expires_at)
    if not db_session.is_active or (session_expires_at and session_expires_at <= now):
        db_session.is_active = 0
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired.",
        )

    last_activity = _to_utc(db_session.last_activity)
    if not last_activity or (now - last_activity).total_seconds() >= SESSION_ACTIVITY_UPDATE_SECONDS:
        db_session.last_activity = now
        db.commit()

    return user


@auth_router.get("/csrf")
def csrf_token(response: Response):
    token = issue_csrf_token()
    _set_csrf_cookie(response, token)
    return {"success": True, "message": "CSRF token issued.", "data": {"csrf_token": token}}


@auth_router.post("/signup", response_model=AuthResponse)
def signup(
    request: SignupRequest,
    http_request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    ip, ua = _get_client_info(http_request)
    normalized_email = request.email.lower().strip()

    _reject_if_rate_limited("signup_ip", ip or "unknown", 10, 600)
    _reject_if_rate_limited("signup_email", normalized_email, 5, 600)

    if request.password != request.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match.")

    ok, error_msg = validate_password_strength(request.password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    existing = db.query(UserRow).filter(UserRow.email == normalized_email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")

    user = UserRow(
        email=normalized_email,
        hashed_password=hash_password(request.password),
        role=request.role,
        name=request.name or normalized_email.split("@", 1)[0],
        created_at=datetime.now(timezone.utc),
        is_verified=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token, refresh_token, _ = _create_user_session(
        db, user, bool(request.remember_me), ip, ua
    )
    _set_auth_cookies(response, access_token, refresh_token, bool(request.remember_me))

    log_audit_event(db, "SIGNUP", f"User signed up: {normalized_email}", user.id, ip, ua)
    db.commit()

    built_user = _build_user_response(user)
    return {
        "success": True,
        "message": "Signup successful.",
        "user": built_user,
        "token": None,
        "data": {"user": built_user},
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
    generic_error = "Invalid email or password."

    _reject_if_rate_limited("login_ip", ip or "unknown", 25, 300)
    _reject_if_rate_limited("login_email", normalized_email, 10, 300)

    user = db.query(UserRow).filter(UserRow.email == normalized_email).first()
    if not user:
        verify_password_with_timing_defense(request.password, None)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=generic_error)

    if user.lockout_until and user.lockout_until > datetime.now(timezone.utc):
        log_security_event(
            db,
            "BRUTE_FORCE",
            "high",
            f"Blocked login attempt on locked account: {normalized_email}",
            user.id,
            ip,
            ua,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=generic_error)

    if request.role != user.role:
        verify_password_with_timing_defense(request.password, user.hashed_password)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=generic_error)

    if not verify_password_with_timing_defense(request.password, user.hashed_password):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        log_audit_event(db, "FAILED_LOGIN", f"Failed login attempt for {normalized_email}", user.id, ip, ua)
        if user.failed_login_attempts >= 5:
            user.lockout_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            log_security_event(
                db,
                "BRUTE_FORCE",
                "high",
                f"Account locked due to repeated login failures: {normalized_email}",
                user.id,
                ip,
                ua,
            )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=generic_error)

    user.failed_login_attempts = 0
    user.lockout_until = None
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    access_token, refresh_token, _ = _create_user_session(
        db, user, bool(request.remember_me), ip, ua
    )
    _set_auth_cookies(response, access_token, refresh_token, bool(request.remember_me))

    log_audit_event(db, "LOGIN", f"User logged in: {normalized_email}", user.id, ip, ua)
    db.commit()

    built_user = _build_user_response(user)
    return {
        "success": True,
        "message": "Login successful.",
        "user": built_user,
        "token": None,
        "data": {"user": built_user},
    }


@auth_router.get("/me")
def me(request: Request, response: Response, db: Session = Depends(get_db)):
    user = _resolve_current_user(request, db)
    if not request.cookies.get(CSRF_COOKIE_NAME):
        _set_csrf_cookie(response, issue_csrf_token())
    built_user = _build_user_response(user)
    return {
        "success": True,
        "message": "Current session loaded.",
        "user": built_user,
        "data": {"user": built_user},
    }


@auth_router.get("/sessions")
def list_sessions(request: Request, db: Session = Depends(get_db)):
    user = _resolve_current_user(request, db)
    sessions = (
        db.query(SessionRow)
        .filter(SessionRow.user_id == user.id, SessionRow.is_active == 1)
        .order_by(SessionRow.last_activity.desc())
        .all()
    )
    current_token = extract_token(request)
    current_session_id = None
    if current_token:
        try:
            current_session_id = decode_token(current_token, "access").get("session_id")
        except ValueError:
            current_session_id = None
    return {
        "success": True,
        "message": "Active sessions loaded.",
        "data": {
            "sessions": [
                {
                    "session_id": session.session_id,
                    "created_at": _to_utc(session.created_at).isoformat() if session.created_at else None,
                    "last_activity": _to_utc(session.last_activity).isoformat() if session.last_activity else None,
                    "expires_at": _to_utc(session.expires_at).isoformat() if session.expires_at else None,
                    "user_agent": session.user_agent,
                    "ip_address": session.ip_address,
                    "remember_me": bool(session.remember_me),
                    "is_current": session.session_id == current_session_id,
                }
                for session in sessions
            ]
        },
    }


@auth_router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    ip, ua = _get_client_info(request)
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is missing.")

    _reject_if_rate_limited("refresh_ip", ip or "unknown", 40, 300)

    try:
        payload = decode_token(refresh_token, "refresh")
    except ValueError as exc:
        _clear_auth_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    user_id = payload.get("sub")
    session_id = payload.get("session_id")
    if not user_id or not session_id:
        _clear_auth_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token payload.")

    user = db.query(UserRow).filter(UserRow.id == int(user_id)).first()
    db_session = db.query(SessionRow).filter(SessionRow.session_id == session_id).first()
    token_hash = _hash_token(refresh_token)
    db_token = db.query(RefreshTokenRow).filter(RefreshTokenRow.token_hash == token_hash).first()

    if not user or not db_session or not db_token or not db_session.is_active:
        _clear_auth_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Active session not found.")

    now = datetime.now(timezone.utc)
    session_expires_at = _to_utc(db_session.expires_at)
    token_expires_at = _to_utc(db_token.expires_at)
    if (session_expires_at and session_expires_at <= now) or (token_expires_at and token_expires_at <= now):
        db_session.is_active = 0
        db_token.is_revoked = 1
        db.commit()
        _clear_auth_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has expired.")

    if db_token.is_revoked:
        db.query(SessionRow).filter(SessionRow.user_id == user.id).update({"is_active": 0})
        db.query(RefreshTokenRow).filter(RefreshTokenRow.user_id == user.id).update({"is_revoked": 1})
        log_security_event(
            db,
            "JWT_REPLAY",
            "critical",
            f"Refresh token replay detected for {user.email}",
            user.id,
            ip,
            ua,
        )
        db.commit()
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked due to a security violation.",
        )

    db_token.is_revoked = 1
    db_session.last_activity = now

    remember_me = bool(db_session.remember_me)
    refresh_expiry = timedelta(
        days=REFRESH_TOKEN_REMEMBER_ME_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS
    )

    new_access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role or "student",
            "session_id": session_id,
        }
    )
    new_refresh_token = create_refresh_token(
        {"sub": str(user.id), "session_id": session_id},
        expires_delta=refresh_expiry,
    )

    db.add(
        RefreshTokenRow(
            user_id=user.id,
            session_id=session_id,
            token_hash=_hash_token(new_refresh_token),
            created_at=now,
            expires_at=now + refresh_expiry,
            is_revoked=0,
        )
    )
    db.commit()

    _set_auth_cookies(response, new_access_token, new_refresh_token, remember_me)
    built_user = _build_user_response(user)
    return {
        "success": True,
        "message": "Token refreshed successfully.",
        "user": built_user,
        "token": None,
        "data": {"user": built_user},
    }


@auth_router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    ip, ua = _get_client_info(request)
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if refresh_token:
        try:
            payload = decode_token(refresh_token, "refresh")
            session_id = payload.get("session_id")
            if session_id:
                db.query(SessionRow).filter(SessionRow.session_id == session_id).update({"is_active": 0})
                db.query(RefreshTokenRow).filter(RefreshTokenRow.session_id == session_id).update({"is_revoked": 1})
                user_id = int(payload.get("sub", 0))
                if user_id:
                    log_audit_event(db, "LOGOUT", "User logged out current session.", user_id, ip, ua)
                db.commit()
        except Exception:
            db.rollback()
    _clear_auth_cookies(response)
    return {"success": True, "message": "Logged out successfully."}


@auth_router.post("/logout/all")
def logout_all_devices(request: Request, response: Response, db: Session = Depends(get_db)):
    ip, ua = _get_client_info(request)
    user = _resolve_current_user(request, db)
    db.query(SessionRow).filter(SessionRow.user_id == user.id).update({"is_active": 0})
    db.query(RefreshTokenRow).filter(RefreshTokenRow.user_id == user.id).update({"is_revoked": 1})
    log_audit_event(db, "LOGOUT_ALL", "User logged out all devices.", user.id, ip, ua)
    db.commit()
    _clear_auth_cookies(response)
    return {"success": True, "message": "Logged out from all devices successfully."}


@auth_router.get("/google/status")
def google_oauth_status(response: Response):
    if not response.headers.get("set-cookie"):
        _set_csrf_cookie(response, issue_csrf_token())
    return {
        "configured": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        "redirect_uri": GOOGLE_REDIRECT_URI,
    }


@auth_router.get("/google")
def google_oauth(role: Optional[str] = "student", next: Optional[str] = "login"):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return RedirectResponse(
            f"{FRONTEND_URL.rstrip('/')}/{(next or 'login')}?error=Google OAuth is not configured on the server",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    signed_state = create_oauth_state(role or "student", next or "login")
    query = urlencode(
        {
            "response_type": "code",
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "scope": "openid email profile",
            "state": signed_state,
            "access_type": "online",
            "prompt": "select_account",
        }
    )
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{query}")


@auth_router.get("/google/callback")
def google_oauth_callback(
    request: Request,
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
            state_data = decode_oauth_state(state)
            role = state_data.get("role", "student")
            next_page = state_data.get("next", "login")
        except ValueError:
            return RedirectResponse(f"{FRONTEND_URL.rstrip('/')}/login?error=Invalid Google sign-in state")

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
            hashed_password=hash_password(str(uuid4())),
            role=role,
            name=profile.get("name") or email.split("@", 1)[0],
            created_at=datetime.now(timezone.utc),
            is_verified=1,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    access_token, refresh_token, _ = _create_user_session(db, user, True, ip, ua)

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
    db.commit()
    return redirect_response
