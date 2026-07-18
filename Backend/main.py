"""ImpactAI FastAPI application entry point."""

from datetime import datetime, timezone
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import CORS_ORIGINS, GROQ_API_KEY
from database import SessionLocal, init_db
from routes.analytics import router as analytics_router
from routes.auth import auth_router
from routes.chat import chat_router
from routes.mood import mood_router
from services.logging import log_security_event
from services.security import validate_csrf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("impactai")

app = FastAPI(
    title="ImpactAI Backend",
    description=(
        "Production-ready Python backend for ImpactAI with local SQLite storage, "
        "Groq AI chat, ML severity classification, and analytics."
    ),
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
)

_CSRF_EXEMPT_PATHS = {
    "/health",
    "/auth/login",
    "/auth/signup",
    "/auth/google",
    "/auth/google/callback",
    "/auth/google/status",
    "/auth/csrf",
    "/api/auth/login",
    "/api/auth/signup",
    "/api/auth/google",
    "/api/auth/google/callback",
    "/api/auth/google/status",
    "/api/auth/csrf",
}


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    if request.method not in {"GET", "HEAD", "OPTIONS"} and request.url.path not in _CSRF_EXEMPT_PATHS:
        if request.cookies.get("access_token") or request.cookies.get("refresh_token"):
            try:
                validate_csrf(request)
            except ValueError:
                db = SessionLocal()
                try:
                    ip = request.client.host if request.client else None
                    log_security_event(
                        db,
                        "CSRF_BLOCKED",
                        "high",
                        f"Blocked request to {request.url.path}",
                        None,
                        ip,
                        request.headers.get("user-agent"),
                    )
                    db.commit()
                finally:
                    db.close()
                return JSONResponse(
                    status_code=403,
                    content={"success": False, "message": "CSRF validation failed.", "errors": ["csrf_validation_failed"]},
                )

    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data: https://*.googleusercontent.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline'; "
        "frame-src 'self' https://accounts.google.com; "
        "connect-src 'self' http://localhost:5000 http://127.0.0.1:5000 http://localhost:8080 http://127.0.0.1:8080 http://localhost:5173 http://127.0.0.1:5173; "
        "object-src 'none'; base-uri 'self'; frame-ancestors 'none';"
    )
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(chat_router, tags=["chat"])
app.include_router(mood_router, tags=["mood"])
app.include_router(analytics_router, tags=["analytics"])


@app.on_event("startup")
def startup_event():
    init_db()
    from services.ml_model import is_model_available

    ml_ok = is_model_available()
    logger.info("=" * 60)
    logger.info("ImpactAI Backend v2.1.0 starting")
    logger.info("  GROQ_API_KEY: %s", "configured" if GROQ_API_KEY else "missing")
    logger.info("  ML Model:     %s", "loaded" if ml_ok else "not available")
    logger.info("=" * 60)


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
        "version": "2.1.0",
        "docs": "/docs",
        "health": "/health",
    }
