"""
ImpactAI — ML Severity Classifier Evaluation and Training Pipeline.

Performs:
1. Complete Dataset Audit (records, duplicates, nulls, class distribution)
2. Train/Test Stratified Split (80/20) with NO data leakage
3. TF-IDF Vectorizer fit exclusively on train set
4. Model evaluation:
   - Accuracy, Macro F1, Weighted F1
   - Per-class Precision, Recall, F1
   - Confusion Matrix
   - Crisis False Negative Rate
5. Saves clean model artifacts for scikit-learn 1.3.2
"""

import json
import pickle
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "train.csv"
MODEL_DIR = BASE_DIR / "ml_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "severity_model.pkl"
VECTORIZER_PATH = MODEL_DIR / "tfidf_vectorizer.pkl"
METRICS_PATH = MODEL_DIR / "model_metrics.json"

CRISIS_PATTERNS = [
    r"\bsuicid\w*\b",
    r"\bkill\s+(my|your|one)?self\b",
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


def run_pipeline():
    print("=" * 65)
    print("  ImpactAI ML Severity Classifier - Audit & Retraining")
    print("=" * 65)

    # 1. Dataset Audit
    df_raw = pd.read_csv(DATA_PATH)
    total_raw_rows = len(df_raw)
    null_contexts = df_raw["Context"].isna().sum()
    null_responses = df_raw["Response"].isna().sum()
    duplicate_rows = df_raw.duplicated(subset=["Context"]).sum()

    print(f"\n[1] DATASET AUDIT:")
    print(f"    Total Rows in train.csv: {total_raw_rows:,}")
    print(f"    Missing 'Context':       {null_contexts}")
    print(f"    Missing 'Response':      {null_responses}")
    print(f"    Duplicate Contexts:      {duplicate_rows} ({duplicate_rows / total_raw_rows * 100:.1f}%)")

    # Use Context as feature target (matches inference time user messages)
    df = df_raw.dropna(subset=["Context"]).copy()
    df["clean_text"] = df["Context"].astype(str).str.strip()
    df = df[df["clean_text"].str.len() > 0]

    df["severity"] = df["clean_text"].apply(assign_severity)
    class_counts = df["severity"].value_counts().to_dict()

    print(f"\n[2] CLASS DISTRIBUTION (on student inquiry texts):")
    for cls, cnt in class_counts.items():
        print(f"    {cls:>8s}: {cnt:>5,}  ({cnt / len(df) * 100:.1f}%)")

    # 2. Stratified Train / Test Split (Strict Leakage Prevention)
    print(f"\n[3] TRAIN / TEST SPLIT (80/20 Stratified):")
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        df["clean_text"],
        df["severity"],
        test_size=0.20,
        random_state=42,
        stratify=df["severity"],
    )
    print(f"    Train size: {len(X_train_raw):,}")
    print(f"    Test size:  {len(X_test_raw):,}")

    # 3. Vectorizer: Fit ONLY on Training Data
    print(f"\n[4] VECTORIZATION (TF-IDF fitted exclusively on train set):")
    vectorizer = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),
        stop_words="english",
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
    )
    X_train = vectorizer.fit_transform(X_train_raw)
    X_test = vectorizer.transform(X_test_raw)
    print(f"    Vocabulary size: {len(vectorizer.vocabulary_):,} features")

    # 4. Logistic Regression Training (Balanced Class Weights)
    print(f"\n[5] MODEL TRAINING (Logistic Regression, multi-class):")
    model = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        C=1.0,
        solver="lbfgs",
        random_state=42,
    )
    model.fit(X_train, y_train)

    # 5. Comprehensive Evaluation on Unseen Test Data
    y_pred = model.predict(X_test)
    acc = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro"))
    weighted_f1 = float(f1_score(y_test, y_pred, average="weighted"))

    labels = sorted(list(df["severity"].unique()))
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    report_dict = classification_report(y_test, y_pred, labels=labels, output_dict=True)

    print(f"\n[6] EVALUATION METRICS ON UNSEEN TEST DATA:")
    print(f"    Accuracy:     {acc * 100:.2f}%")
    print(f"    Macro F1:     {macro_f1:.4f}")
    print(f"    Weighted F1:  {weighted_f1:.4f}")
    print(f"\n    Per-Class Classification Report:")
    print(classification_report(y_test, y_pred, labels=labels))

    print(f"    Confusion Matrix (Labels: {labels}):")
    for idx, row in enumerate(cm):
        print(f"      {labels[idx]:>8s}: {row.tolist()}")

    # Crisis class false-negative rate calculation
    crisis_idx = labels.index("crisis") if "crisis" in labels else -1
    if crisis_idx >= 0:
        actual_crisis_count = int(cm[crisis_idx].sum())
        crisis_true_positive = int(cm[crisis_idx][crisis_idx])
        crisis_false_negative = actual_crisis_count - crisis_true_positive
        crisis_fn_rate = crisis_false_negative / actual_crisis_count if actual_crisis_count > 0 else 0.0
        print(f"\n    Crisis Class Metrics:")
        print(f"      Actual Crisis in Test: {actual_crisis_count}")
        print(f"      True Positives:        {crisis_true_positive}")
        print(f"      False Negatives:       {crisis_false_negative}")
        print(f"      Crisis FN Rate:        {crisis_fn_rate * 100:.2f}%")
    else:
        crisis_fn_rate = 0.0

    # 6. Save Clean Model Artifacts
    print(f"\n[7] SAVING CLEAN ARTIFACTS TO {MODEL_DIR} ...")
    with open(VECTORIZER_PATH, "wb") as f:
        pickle.dump(vectorizer, f, protocol=pickle.HIGHEST_PROTOCOL)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)

    metrics_payload = {
        "dataset": {
            "total_rows": total_raw_rows,
            "used_rows": len(df),
            "duplicates": int(duplicate_rows),
            "class_distribution": class_counts,
        },
        "evaluation": {
            "accuracy": acc,
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1,
            "labels": labels,
            "confusion_matrix": cm.tolist(),
            "classification_report": report_dict,
            "crisis_false_negative_rate": crisis_fn_rate,
        },
        "model_version": "2.1.0-scikit1.3.2",
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics_payload, f, indent=2)

    print("    Model artifacts and model_metrics.json saved successfully.")
    print("=" * 65)


if __name__ == "__main__":
    run_pipeline()
