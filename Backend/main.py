"""
ImpactAI — FastAPI application entry‑point.

Run with:
    uvicorn main:app --host 0.0.0.0 --port 5000 --reload
"""

from datetime import datetime, timezone
import logging

# Configure logging so messages show in Render's log viewer
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("impactai")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS, GROQ_API_KEY
from database import init_db
from routes.analytics import router as analytics_router
from routes.auth import auth_router
from routes.chat import chat_router
from routes.mood import mood_router

app = FastAPI(
    title="ImpactAI Backend",
    description=(
        "Production‑ready Python backend for ImpactAI — "
        "local SQLite database, Groq Cloud AI chat, ML severity classifier, "
        "and analytics visualizations."
    ),
    version="2.0.0",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Route registration ────────────────────────────────────────────────────────
# Auth routes available at both / and /api/auth for frontend compatibility
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

# Chat & Mood (no prefix — frontend calls /chat directly)
app.include_router(chat_router, tags=["chat"])
app.include_router(mood_router, tags=["mood"])

# Analytics
app.include_router(analytics_router, tags=["analytics"])


# ── Lifecycle ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup_event():
    init_db()
    # Pre‑load ML model at startup (if available)
    from services.ml_model import is_model_available
    ml_ok = is_model_available()

    # Startup diagnostics
    logger.info("=" * 60)
    logger.info("ImpactAI Backend v2.0.0 starting")
    logger.info("  GROQ_API_KEY: %s", "configured ✓" if GROQ_API_KEY else "⚠ MISSING — chat will fail")
    logger.info("  ML Model:     %s", "loaded ✓" if ml_ok else "not available (optional)")
    logger.info("=" * 60)


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "sqlite",
        "ai_provider": "groq",
    }


@app.get("/", tags=["system"])
def root():
    return {
        "name": "ImpactAI Backend",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
    }
