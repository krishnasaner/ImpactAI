from datetime import datetime, timedelta
from typing import Optional

from bson.objectid import ObjectId
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse

from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, JWT_EXPIRATION_HOURS
from database import users_collection
from schemas import AuthResponse, LoginRequest, SignupRequest, UserResponse
from services.security import (
    create_access_token,
    decode_access_token,
    extract_token,
    hash_password,
    verify_password,
)

auth_router = APIRouter()


def _build_user_response(user_doc: dict) -> UserResponse:
    return UserResponse(
        id=str(user_doc["_id"]),
        email=user_doc["email"],
        role=user_doc.get("role", "student"),
        name=user_doc.get("name"),
    )


def _set_token_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=int(timedelta(hours=JWT_EXPIRATION_HOURS).total_seconds()),
    )


@auth_router.post("/signup", response_model=AuthResponse)
def signup(request: SignupRequest, response: Response):
    normalized_email = request.email.lower().strip()
    existing = users_collection.find_one({"email": normalized_email})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")

    hashed_password = hash_password(request.password)
    user_doc = {
        "email": normalized_email,
        "hashed_password": hashed_password,
        "role": request.role,
        "name": request.name or normalized_email.split("@", 1)[0],
        "created_at": datetime.utcnow(),
    }
    new_user = users_collection.insert_one(user_doc)
    token = create_access_token({"sub": str(new_user.inserted_id), "email": normalized_email, "role": request.role})

    _set_token_cookie(response, token)
    return {"user": _build_user_response(user_doc), "token": token}


@auth_router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, response: Response):
    normalized_email = request.email.lower().strip()
    user_doc = users_collection.find_one({"email": normalized_email})
    if not user_doc or not verify_password(request.password, user_doc.get("hashed_password", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    token = create_access_token({"sub": str(user_doc["_id"]), "email": normalized_email, "role": user_doc.get("role", "student")})
    _set_token_cookie(response, token)

    return {
        "user": _build_user_response(user_doc),
        "token": token,
    }


def _resolve_current_user(request: Request) -> dict:
    token = extract_token(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication credentials were not provided.")

    try:
        payload = decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token.")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    user_doc = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    return user_doc


@auth_router.get("/me")
def me(request: Request):
    user_doc = _resolve_current_user(request)
    return {"user": _build_user_response(user_doc)}


@auth_router.get("/google")
def google_oauth(role: Optional[str] = "student"):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return HTMLResponse(
            content=(
                "<h1>Google OAuth is not configured.</h1>"
                "<p>Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in Backend/.env.</p>"
            ),
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
        )

    query = (
        f"response_type=code&client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20email%20profile&"
        f"state={role}"
    )
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{query}")
