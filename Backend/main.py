from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS
from database import init_indexes
from routes.analytics import router as analytics_router
from routes.auth import auth_router
from routes.chat import chat_router

app = FastAPI(
    title="ImpactAI Backend",
    description="Python backend for ImpactAI with MongoDB Atlas, AI chat, and analytics visualizations.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(auth_router, prefix="/api/auth")
app.include_router(chat_router)
app.include_router(analytics_router)


@app.on_event("startup")
def startup_event():
    init_indexes()


@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
