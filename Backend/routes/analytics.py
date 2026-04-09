"""
ImpactAI — Analytics routes.

GET /analytics/stats    →  JSON summary of the training data
GET /analytics/plot     →  PNG histogram image
GET /analytics/db-stats →  Live stats from the SQLite database
GET /analytics/ml-info  →  ML model metadata
"""

import io
from pathlib import Path
from typing import Dict

import matplotlib
matplotlib.use("Agg")  # non‑interactive backend (no GUI)
import matplotlib.pyplot as plt
import pandas as pd
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from config import TRAIN_CSV_PATH
from database import get_db, ChatSessionRow, UserRow, MoodEntryRow
from services.ml_model import get_model_info

router = APIRouter()


# ═══════════════════ Training‑data stats (from CSV) ═══════════════════════════

def _load_data() -> pd.DataFrame:
    return pd.read_csv(TRAIN_CSV_PATH)


def _build_length_distribution(series: pd.Series) -> Dict[str, int]:
    lengths = series.str.split().str.len()
    distribution = lengths.value_counts().sort_index().head(50).to_dict()
    return {str(k): int(v) for k, v in distribution.items()}


@router.get("/analytics/stats")
def analytics_stats():
    df = _load_data()
    context_lengths = df["Context"].astype(str).str.split().str.len()
    response_lengths = df["Response"].astype(str).str.split().str.len()

    return JSONResponse(content={
        "row_count": int(df.shape[0]),
        "average_context_tokens": round(float(context_lengths.mean()), 2),
        "average_response_tokens": round(float(response_lengths.mean()), 2),
        "context_length_distribution": _build_length_distribution(
            df["Context"].astype(str)
        ),
        "response_length_distribution": _build_length_distribution(
            df["Response"].astype(str)
        ),
    })


# ═══════════════════ Training‑data plot (PNG) ═════════════════════════════════

@router.get("/analytics/plot")
def analytics_plot():
    df = _load_data()
    context_lengths = df["Context"].astype(str).str.split().str.len()
    response_lengths = df["Response"].astype(str).str.split().str.len()

    plt.style.use("seaborn-v0_8")
    fig, axes = plt.subplots(2, 1, figsize=(10, 10), tight_layout=True)

    axes[0].hist(
        context_lengths, bins=30, color="#4f46e5", edgecolor="#ffffff", alpha=0.85
    )
    axes[0].set_title("Context Length Distribution", fontsize=14, fontweight="bold")
    axes[0].set_xlabel("Word count")
    axes[0].set_ylabel("Examples")

    axes[1].hist(
        response_lengths, bins=30, color="#14b8a6", edgecolor="#ffffff", alpha=0.85
    )
    axes[1].set_title("Response Length Distribution", fontsize=14, fontweight="bold")
    axes[1].set_xlabel("Word count")
    axes[1].set_ylabel("Examples")

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150)
    buffer.seek(0)
    plt.close(fig)

    return Response(content=buffer.getvalue(), media_type="image/png")


# ═══════════════════ Live DB stats ════════════════════════════════════════════

@router.get("/analytics/db-stats")
def db_stats(db: Session = Depends(get_db)):
    total_users = db.query(func.count(UserRow.id)).scalar() or 0
    total_chats = db.query(func.count(ChatSessionRow.id)).scalar() or 0
    total_moods = db.query(func.count(MoodEntryRow.id)).scalar() or 0

    # Severity breakdown from chat history
    severity_breakdown = {}
    rows = (
        db.query(ChatSessionRow.severity, func.count(ChatSessionRow.id))
        .group_by(ChatSessionRow.severity)
        .all()
    )
    for sev, cnt in rows:
        severity_breakdown[sev or "unknown"] = cnt

    # Role breakdown
    role_breakdown = {}
    rows = (
        db.query(UserRow.role, func.count(UserRow.id))
        .group_by(UserRow.role)
        .all()
    )
    for role, cnt in rows:
        role_breakdown[role or "unknown"] = cnt

    return {
        "total_users": total_users,
        "total_chats": total_chats,
        "total_moods": total_moods,
        "severity_breakdown": severity_breakdown,
        "role_breakdown": role_breakdown,
    }


# ═══════════════════ ML model info ════════════════════════════════════════════

@router.get("/analytics/ml-info")
def ml_info():
    info = get_model_info()
    if info is None:
        return JSONResponse(
            status_code=200,
            content={
                "loaded": False,
                "message": "No ML model found. Run  python scripts/train_model.py  to train one.",
            },
        )
    return {"loaded": True, **info}
