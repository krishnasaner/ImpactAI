"""
ImpactAI — centralised configuration.

All settings are loaded from environment variables (via .env) with sensible
defaults so the application works out‑of‑the‑box with a local SQLite database
and a Groq Cloud API key.
"""

from pathlib import Path
from dotenv import load_dotenv
import os

# ── paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ── database (SQLite — stored locally) ─────────────────────────────────────────
DATABASE_PATH = BASE_DIR / "data" / "impactai.db"

# ── JWT auth ───────────────────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "impactai_jwt_secret_key_change_in_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# ── CORS ───────────────────────────────────────────────────────────────────────
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8080,http://localhost:5173,http://localhost:5000,http://localhost:3000",
    ).split(",")
    if origin.strip()
]

# ── Groq Cloud AI ──────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ── ML model ───────────────────────────────────────────────────────────────────
ML_MODEL_PATH = BASE_DIR / "ml_models" / "severity_model.pkl"
ML_VECTORIZER_PATH = BASE_DIR / "ml_models" / "tfidf_vectorizer.pkl"

# ── Google OAuth (optional) ────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/google/callback"
)

# ── Training data ──────────────────────────────────────────────────────────────
TRAIN_CSV_PATH = BASE_DIR / "data" / "train.csv"
