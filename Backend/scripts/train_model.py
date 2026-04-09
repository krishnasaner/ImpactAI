"""
ImpactAI — Train the ML severity classifier.

This script:
 1. Loads the mental‑health counseling dataset (train.csv)
 2. Assigns severity labels based on keyword heuristics
    (the original data doesn't have severity ground‑truth,
     so we create synthetic labels from known mental‑health
     terminology)
 3. Trains a TF‑IDF → Logistic Regression pipeline
 4. Evaluates the model (accuracy, classification report, confusion matrix)
 5. Saves the trained artefacts to  Backend/ml_models/

Run:
    cd Backend
    python scripts/train_model.py
"""

import re
import sys
from pathlib import Path

import pandas as pd
import numpy as np
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

# ── Resolve paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "train.csv"
MODEL_DIR = BASE_DIR / "ml_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "severity_model.pkl"
VECTORIZER_PATH = MODEL_DIR / "tfidf_vectorizer.pkl"
PLOTS_DIR = BASE_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════ Severity labeller ════════════════════════════════

# Keyword sets used to derive synthetic severity labels from the text content.
# Each entry is (pattern, label, priority) — higher priority wins.
CRISIS_PATTERNS = [
    r"\bsuicid\w*\b",
    r"\bkill\s+(my|your)self\b",
    r"\bself[- ]?harm\b",
    r"\bending\s+(my|it|life)\b",
    r"\bdon'?t\s+want\s+to\s+live\b",
    r"\bwant\s+to\s+die\b",
    r"\b988\b",
    r"\bcrisis\s+line\b",
    r"\bemergency\b",
]

HIGH_PATTERNS = [
    r"\bsexual\s+abuse\b",
    r"\babuse\b",
    r"\btrauma\b",
    r"\bPTSD\b",
    r"\bworthless\b",
    r"\bhopeless\b",
    r"\bpanic\s+attack\b",
    r"\bsevere\s+(depression|anxiety)\b",
    r"\bcan'?t\s+stop\s+crying\b",
    r"\bcut(ting)?\s+(my|your)self\b",
    r"\bhurt\s+(my|your)self\b",
]

MEDIUM_PATTERNS = [
    r"\bdepress(ed|ion)?\b",
    r"\banxi(ous|ety)\b",
    r"\bstress(ed)?\b",
    r"\boverwhelm(ed|ing)?\b",
    r"\binsomnia\b",
    r"\bcan'?t\s+sleep\b",
    r"\blow\s+self[- ]?esteem\b",
    r"\bsad(ness)?\b",
    r"\blonely\b",
    r"\bgrief\b",
    r"\bloss\b",
    r"\bdivorce\b",
    r"\brelationship\s+problem\b",
]


def _assign_severity(text: str) -> str:
    """Assign a severity label based on keyword matching."""
    text_lower = str(text).lower()
    for pattern in CRISIS_PATTERNS:
        if re.search(pattern, text_lower):
            return "crisis"
    for pattern in HIGH_PATTERNS:
        if re.search(pattern, text_lower):
            return "high"
    for pattern in MEDIUM_PATTERNS:
        if re.search(pattern, text_lower):
            return "medium"
    return "low"


# ═══════════════════════════ Main training flow ═══════════════════════════════

def main():
    print("=" * 60)
    print("  ImpactAI — ML Severity Classifier Training")
    print("=" * 60)

    # ── 1. Load data ───────────────────────────────────────────────────────
    print(f"\n[1/6] Loading data from {DATA_PATH} ...")
    df = pd.read_csv(DATA_PATH)
    print(f"       Rows: {len(df):,}")

    # Combine Context + Response for richer features
    df["text"] = df["Context"].astype(str) + " " + df["Response"].astype(str)
    df["text"] = df["text"].str.strip()

    # ── 2. Assign severity labels ──────────────────────────────────────────
    print("[2/6] Assigning severity labels (keyword heuristics) ...")
    df["severity"] = df["text"].apply(_assign_severity)

    label_counts = df["severity"].value_counts()
    print(f"\n       Label distribution:")
    for label, count in label_counts.items():
        print(f"         {label:>8s}: {count:>5,}  ({count / len(df) * 100:.1f}%)")

    # ── 3. Vectorize ───────────────────────────────────────────────────────
    print("\n[3/6] Vectorizing text with TF‑IDF (max_features=10000) ...")
    vectorizer = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),
        stop_words="english",
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
    )
    X = vectorizer.fit_transform(df["text"])
    y = df["severity"]

    # ── 4. Train / test split ──────────────────────────────────────────────
    print("[4/6] Splitting data (80% train / 20% test) ...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"       Train: {X_train.shape[0]:,}   Test: {X_test.shape[0]:,}")

    # ── 5. Train model ─────────────────────────────────────────────────────
    print("[5/6] Training Logistic Regression (multi‑class, balanced) ...")
    model = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        C=1.0,
        solver="lbfgs",
        multi_class="multinomial",
        random_state=42,
    )
    model.fit(X_train, y_train)

    # Cross‑validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
    print(f"       5‑fold CV accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # ── 6. Evaluate ────────────────────────────────────────────────────────
    print("\n[6/6] Evaluating on test set ...")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n       Test Accuracy: {accuracy:.4f}")
    print(f"\n{classification_report(y_test, y_pred, zero_division=0)}")

    # Confusion matrix plot
    cm = confusion_matrix(y_test, y_pred, labels=model.classes_)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=model.classes_,
        yticklabels=model.classes_,
        ax=ax,
    )
    ax.set_title("Severity Model — Confusion Matrix", fontsize=14, fontweight="bold")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    cm_path = PLOTS_DIR / "confusion_matrix.png"
    fig.savefig(cm_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\n       Confusion matrix saved → {cm_path}")

    # Label distribution plot
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    colors = {"low": "#22c55e", "medium": "#eab308", "high": "#f97316", "crisis": "#ef4444"}
    bars = label_counts.plot(
        kind="bar",
        color=[colors.get(l, "#6366f1") for l in label_counts.index],
        edgecolor="white",
        ax=ax2,
    )
    ax2.set_title("Severity Label Distribution", fontsize=14, fontweight="bold")
    ax2.set_xlabel("Severity")
    ax2.set_ylabel("Count")
    ax2.tick_params(axis="x", rotation=0)
    dist_path = PLOTS_DIR / "severity_distribution.png"
    fig2.savefig(dist_path, dpi=150, bbox_inches="tight")
    plt.close(fig2)
    print(f"       Label distribution plot saved → {dist_path}")

    # ── Save artefacts ─────────────────────────────────────────────────────
    with open(VECTORIZER_PATH, "wb") as f:
        pickle.dump(vectorizer, f)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    print(f"\n  ✅  Vectorizer saved → {VECTORIZER_PATH}")
    print(f"  ✅  Model saved      → {MODEL_PATH}")
    print("=" * 60)
    print("  Training complete! The model will auto‑load when you start the server.")
    print("=" * 60)


if __name__ == "__main__":
    main()
