"""
ImpactAI centralized configuration.

All settings are loaded from environment variables (via .env) with sensible
local defaults so the application can run in development or verification mode.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DATABASE_PATH = Path(
    os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "impactai.db"))
).resolve()

JWT_SECRET = os.getenv("JWT_SECRET", "impactai_jwt_secret_key_change_in_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REFRESH_TOKEN_REMEMBER_ME_DAYS = int(
    os.getenv("REFRESH_TOKEN_REMEMBER_ME_DAYS", "30")
)
AUTH_COOKIE_DOMAIN = os.getenv("AUTH_COOKIE_DOMAIN") or None
ACCESS_COOKIE_NAME = os.getenv("ACCESS_COOKIE_NAME", "access_token")
REFRESH_COOKIE_NAME = os.getenv("REFRESH_COOKIE_NAME", "refresh_token")
CSRF_COOKIE_NAME = os.getenv("CSRF_COOKIE_NAME", "csrf_token")
CSRF_HEADER_NAME = os.getenv("CSRF_HEADER_NAME", "X-CSRF-Token")
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "").lower() == "true"
SESSION_ACTIVITY_UPDATE_SECONDS = int(
    os.getenv("SESSION_ACTIVITY_UPDATE_SECONDS", "60")
)

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8080,http://localhost:5173,http://localhost:5000,http://localhost:3000",
    ).split(",")
    if origin.strip()
]

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

ML_MODEL_PATH = BASE_DIR / "ml_models" / "severity_model.pkl"
ML_VECTORIZER_PATH = BASE_DIR / "ml_models" / "tfidf_vectorizer.pkl"

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/google/callback"
)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN") or AUTH_COOKIE_DOMAIN
GOOGLE_OAUTH_STATE_TTL_SECONDS = int(
    os.getenv("GOOGLE_OAUTH_STATE_TTL_SECONDS", "600")
)

TRAIN_CSV_PATH = BASE_DIR / "data" / "train.csv"
