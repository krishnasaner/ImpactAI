import io
from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd
from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

router = APIRouter()
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "train.csv"


def _load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH)


def _build_length_distribution(series: pd.Series) -> Dict[str, int]:
    lengths = series.str.split().str.len()
    distribution = lengths.value_counts().sort_index().to_dict()
    return {str(k): int(v) for k, v in distribution.items()}


@router.get("/analytics/stats")
def analytics_stats():
    df = _load_data()
    context_lengths = df["Context"].astype(str).str.split().str.len()
    response_lengths = df["Response"].astype(str).str.split().str.len()

    return JSONResponse(
        content={
            "row_count": int(df.shape[0]),
            "average_context_tokens": float(context_lengths.mean()),
            "average_response_tokens": float(response_lengths.mean()),
            "context_length_distribution": _build_length_distribution(df["Context"].astype(str)),
            "response_length_distribution": _build_length_distribution(df["Response"].astype(str)),
        }
    )


@router.get("/analytics/plot")
def analytics_plot():
    df = _load_data()
    context_lengths = df["Context"].astype(str).str.split().str.len()
    response_lengths = df["Response"].astype(str).str.split().str.len()

    plt.style.use("seaborn-v0_8")
    fig, axes = plt.subplots(2, 1, figsize=(10, 10), tight_layout=True)

    axes[0].hist(context_lengths, bins=30, color="#4f46e5", edgecolor="#ffffff", alpha=0.85)
    axes[0].set_title("Context Length Distribution")
    axes[0].set_xlabel("Word count")
    axes[0].set_ylabel("Examples")

    axes[1].hist(response_lengths, bins=30, color="#14b8a6", edgecolor="#ffffff", alpha=0.85)
    axes[1].set_title("Response Length Distribution")
    axes[1].set_xlabel("Word count")
    axes[1].set_ylabel("Examples")

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150)
    buffer.seek(0)
    plt.close(fig)

    return Response(content=buffer.getvalue(), media_type="image/png")
