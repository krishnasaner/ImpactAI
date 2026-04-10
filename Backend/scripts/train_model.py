"""
ImpactAI - Train the ML severity classifier.

This script:
1. Loads the mental health counseling dataset (train.csv)
2. Assigns severity labels based on keyword heuristics
3. Trains a TF-IDF -> Logistic Regression pipeline
4. Evaluates the model
5. Saves the trained artifacts to Backend/ml_models/

Run:
    cd Backend
    python scripts/train_model.py
"""

import pickle
import re
from pathlib import Path

import matplotlib
import pandas as pd
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import cross_val_score, train_test_split

matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "train.csv"
MODEL_DIR = BASE_DIR / "ml_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "severity_model.pkl"
VECTORIZER_PATH = MODEL_DIR / "tfidf_vectorizer.pkl"
PLOTS_DIR = BASE_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


CRISIS_PATTERNS = [
    r"\bsuicid\w*\b",
    r"\bkill\s+(my|your)self\b",
    r"\bself[- ]?harm\b",
    r"\bending\s+(my|it|life)\b",
    r"\bdon'?t\s+want\s+to\s+live\b",
    r"\bwant\s+to\s+die\b",
    r"\b988\b",
    r"\b14416\b",
    r"\b1800[- ]?89[- ]?14416\b",
    r"\baasra\b",
    r"\bcrisis\s+line\b",
    r"\bemergency\b",
    r"\b112\b",
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


def assign_severity(text: str) -> str:
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


def main():
    print("=" * 60)
    print("  ImpactAI - ML Severity Classifier Training")
    print("=" * 60)

    print(f"\n[1/6] Loading data from {DATA_PATH} ...")
    df = pd.read_csv(DATA_PATH)
    print(f"       Rows: {len(df):,}")

    df["text"] = df["Context"].astype(str) + " " + df["Response"].astype(str)
    df["text"] = df["text"].str.strip()
    
    # Handle missing values
    df = df.dropna(subset=["text"])
    df = df[df["text"].str.len() > 0]

    print("[2/6] Assigning severity labels (keyword heuristics) ...")
    df["severity"] = df["text"].apply(assign_severity)

    label_counts = df["severity"].value_counts()
    print("\n       Label distribution:")
    for label, count in label_counts.items():
        print(f"         {label:>8s}: {count:>5,}  ({count / len(df) * 100:.1f}%)")

    print("\n[3/6] Vectorizing text with TF-IDF (max_features=10000) ...")
    vectorizer = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),
        stop_words="english",
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
    )
    x = vectorizer.fit_transform(df["text"])
    y = df["severity"]

    print("[4/6] Splitting data (80% train / 20% test) ...")
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"       Train: {x_train.shape[0]:,}   Test: {x_test.shape[0]:,}")

    print("[5/6] Training Logistic Regression (multi-class, balanced) ...")
    model = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        C=1.0,
        solver="lbfgs",
        random_state=42,
    )
    model.fit(x_train, y_train)

    cv_scores = cross_val_score(model, x, y, cv=5, scoring="accuracy")
    print(f"       5-fold CV accuracy: {cv_scores.mean():.4f} +/- {cv_scores.std():.4f}")

    print("\n[6/6] Evaluating on test set ...")
    y_pred = model.predict(x_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n       Test Accuracy: {accuracy:.4f}")
    print(f"\n{classification_report(y_test, y_pred, zero_division=0)}")

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
    ax.set_title("Severity Model - Confusion Matrix", fontsize=14, fontweight="bold")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    cm_path = PLOTS_DIR / "confusion_matrix.png"
    fig.savefig(cm_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\n       Confusion matrix saved -> {cm_path}")

    fig2, ax2 = plt.subplots(figsize=(8, 5))
    colors = {"low": "#22c55e", "medium": "#eab308", "high": "#f97316", "crisis": "#ef4444"}
    label_counts.plot(
        kind="bar",
        color=[colors.get(label, "#6366f1") for label in label_counts.index],
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
    print(f"       Label distribution plot saved -> {dist_path}")

    with open(VECTORIZER_PATH, "wb") as vectorizer_file:
        pickle.dump(vectorizer, vectorizer_file)
    with open(MODEL_PATH, "wb") as model_file:
        pickle.dump(model, model_file)

    print(f"\n  [ok] Vectorizer saved -> {VECTORIZER_PATH}")
    print(f"  [ok] Model saved      -> {MODEL_PATH}")
    print("=" * 60)
    print("  Training complete! The model will auto-load when you start the server.")
    print("=" * 60)


if __name__ == "__main__":
    main()
