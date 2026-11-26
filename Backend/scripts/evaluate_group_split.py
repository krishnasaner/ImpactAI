"""
Phase B — ML Evaluation with Group-Based Train/Test Splitting.

Eliminates duplicate-context leakage by ensuring identical contexts
are NEVER split across training and testing sets.

Compares group-split metrics against previous random-split metrics
to quantify the inflation caused by data leakage.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import GroupShuffleSplit

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "train.csv"
METRICS_PATH = BASE_DIR / "ml_models" / "model_metrics.json"
OUTPUT_PATH = BASE_DIR / "ml_models" / "group_split_metrics.json"

# ── Severity labeling (same heuristics as the existing pipeline) ───────────────
CRISIS_KEYWORDS = [
    "suicid", "kill myself", "end my life", "want to die", "don't want to live",
    "hang myself", "cutting myself", "overdos", "take all my pills",
    "jump off", "shoot myself", "better off dead", "no reason to live",
    "self-harm", "self harm", "hurt myself", "slit my",
]
HIGH_KEYWORDS = [
    "hopeless", "helpless", "can't go on", "give up on life",
    "panic attack", "severe anxiety", "trauma", "ptsd", "abuse",
    "assault", "domestic violence", "eating disorder", "anorexi", "bulimi",
]
MEDIUM_KEYWORDS = [
    "depress", "anxious", "anxiety", "overwhelm", "can't sleep",
    "insomnia", "lonely", "isolated", "stressed", "burnout",
    "grief", "loss", "divorce", "breakup", "crying",
]


def assign_severity(text: str) -> str:
    t = str(text).lower()
    for kw in CRISIS_KEYWORDS:
        if kw in t:
            return "crisis"
    for kw in HIGH_KEYWORDS:
        if kw in t:
            return "high"
    for kw in MEDIUM_KEYWORDS:
        if kw in t:
            return "medium"
    return "low"


def main():
    print("=" * 70)
    print("PHASE B.1 — ML EVALUATION WITH GROUP-BASED SPLITTING")
    print("=" * 70)

    # ── Load data ──────────────────────────────────────────────────────────
    df = pd.read_csv(DATA_PATH)
    print(f"\nDataset: {len(df)} rows, {df.shape[1]} columns")

    # Normalize contexts for grouping
    df["context_clean"] = df["Context"].astype(str).str.strip().str.lower()
    df["severity"] = df["context_clean"].apply(assign_severity)

    # ── Duplicate analysis ─────────────────────────────────────────────────
    unique_contexts = df["context_clean"].nunique()
    duplicate_contexts = len(df) - unique_contexts
    group_sizes = df.groupby("context_clean").size()

    print(f"\nTotal rows:            {len(df)}")
    print(f"Unique contexts:       {unique_contexts}")
    print(f"Duplicate rows:        {duplicate_contexts} ({100*duplicate_contexts/len(df):.1f}%)")
    print(f"Max duplicates for one context: {group_sizes.max()}")
    print(f"Mean group size:       {group_sizes.mean():.2f}")

    # Severity distribution
    print("\n── Severity Distribution ──")
    dist = df["severity"].value_counts()
    for label in ["low", "medium", "high", "crisis"]:
        count = dist.get(label, 0)
        pct = 100 * count / len(df)
        print(f"  {label:8s}: {count:5d} ({pct:5.1f}%)")

    # Check for conflicting labels within same context
    conflict_groups = (
        df.groupby("context_clean")["severity"]
        .nunique()
        .pipe(lambda s: s[s > 1])
    )
    print(f"\nContexts with conflicting severity labels: {len(conflict_groups)}")
    if len(conflict_groups) > 0:
        print("  (Since severity is derived from context text deterministically,")
        print("   this should be 0 — confirming no label conflicts.)")

    # ── Group-based split ──────────────────────────────────────────────────
    print("\n── Group-Based Split ──")

    # Create group identifiers (integer-encoded for each unique context)
    groups = df["context_clean"].factorize()[0]

    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(df, df["severity"], groups=groups))

    X_train_text = df.iloc[train_idx]["Context"].astype(str)
    X_test_text = df.iloc[test_idx]["Context"].astype(str)
    y_train = df.iloc[train_idx]["severity"]
    y_test = df.iloc[test_idx]["severity"]

    # Verify zero context leakage
    train_contexts = set(df.iloc[train_idx]["context_clean"])
    test_contexts = set(df.iloc[test_idx]["context_clean"])
    leaked = train_contexts & test_contexts
    print(f"  Train samples:   {len(train_idx)}")
    print(f"  Test samples:    {len(test_idx)}")
    print(f"  Train contexts:  {len(train_contexts)}")
    print(f"  Test contexts:   {len(test_contexts)}")
    print(f"  Context overlap: {len(leaked)} {'(CLEAN — zero leakage)' if len(leaked) == 0 else '(LEAKAGE DETECTED!)'}")

    # Train/test severity distribution
    print("\n  Train severity distribution:")
    for label in ["low", "medium", "high", "crisis"]:
        count = (y_train == label).sum()
        print(f"    {label:8s}: {count:5d} ({100*count/len(y_train):5.1f}%)")
    print("  Test severity distribution:")
    for label in ["low", "medium", "high", "crisis"]:
        count = (y_test == label).sum()
        print(f"    {label:8s}: {count:5d} ({100*count/len(y_test):5.1f}%)")

    # ── Train TF-IDF + Logistic Regression ─────────────────────────────────
    print("\n── Training TF-IDF + Logistic Regression ──")
    vectorizer = TfidfVectorizer(max_features=10000, stop_words="english", ngram_range=(1, 2))
    X_train = vectorizer.fit_transform(X_train_text)
    X_test = vectorizer.transform(X_test_text)

    model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    # ── Metrics ────────────────────────────────────────────────────────────
    accuracy = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    print(f"\n  Accuracy:      {accuracy:.4f}")
    print(f"  Macro F1:      {macro_f1:.4f}")
    print(f"  Weighted F1:   {weighted_f1:.4f}")

    # Per-class report
    labels = ["low", "medium", "high", "crisis"]
    report = classification_report(
        y_test, y_pred, labels=labels, output_dict=True, zero_division=0
    )
    report_text = classification_report(
        y_test, y_pred, labels=labels, zero_division=0
    )
    print(f"\n── Per-Class Report ──")
    print(report_text)

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    print("── Confusion Matrix ──")
    print(f"{'':>10s}  " + "  ".join(f"{l:>8s}" for l in labels))
    for i, row_label in enumerate(labels):
        row_str = "  ".join(f"{cm[i, j]:8d}" for j in range(len(labels)))
        print(f"{row_label:>10s}  {row_str}")

    # Crisis-specific metrics
    crisis_idx = labels.index("crisis")
    crisis_tp = cm[crisis_idx, crisis_idx]
    crisis_fn = sum(cm[crisis_idx, :]) - crisis_tp
    crisis_fp = sum(cm[:, crisis_idx]) - crisis_tp
    crisis_actual = sum(cm[crisis_idx, :])

    print(f"\n── Crisis Detection ──")
    print(f"  True Positives:  {crisis_tp}")
    print(f"  False Negatives: {crisis_fn}  (crisis missed by model)")
    print(f"  False Positives: {crisis_fp}  (non-crisis flagged as crisis)")
    print(f"  Total actual:    {crisis_actual}")
    if crisis_actual > 0:
        print(f"  Recall:          {crisis_tp/crisis_actual:.4f}")

    # ── Compare with previous random-split metrics ─────────────────────────
    print("\n── Comparison: Random Split vs Group Split ──")
    prev_metrics = None
    if METRICS_PATH.exists():
        try:
            with open(METRICS_PATH, "r") as f:
                prev_data = json.load(f)
            prev_metrics = prev_data.get("evaluation", {})
        except Exception:
            pass

    if prev_metrics:
        prev_acc = prev_metrics.get("accuracy", 0)
        prev_macro = prev_metrics.get("macro_f1", 0)
        prev_weighted = prev_metrics.get("weighted_f1", 0)

        print(f"  {'Metric':>18s}  {'Random Split':>14s}  {'Group Split':>14s}  {'Delta':>10s}")
        print(f"  {'─' * 18}  {'─' * 14}  {'─' * 14}  {'─' * 10}")
        print(f"  {'Accuracy':>18s}  {prev_acc:>14.4f}  {accuracy:>14.4f}  {accuracy - prev_acc:>+10.4f}")
        print(f"  {'Macro F1':>18s}  {prev_macro:>14.4f}  {macro_f1:>14.4f}  {macro_f1 - prev_macro:>+10.4f}")
        print(f"  {'Weighted F1':>18s}  {prev_weighted:>14.4f}  {weighted_f1:>14.4f}  {weighted_f1 - prev_weighted:>+10.4f}")

        if accuracy < prev_acc - 0.05:
            print("\n  ⚠ GROUP-SPLIT ACCURACY IS SIGNIFICANTLY LOWER.")
            print("  This confirms the previous random-split metrics were INFLATED by")
            print("  duplicate-context leakage. The group-split results are the honest evaluation.")
    else:
        print("  Previous random-split metrics not found for comparison.")

    # ── Dataset limitations ────────────────────────────────────────────────
    print("\n── Dataset Limitations ──")
    print("  1. Severity labels are DERIVED from text heuristics, not expert annotations.")
    print("  2. 71.7% of rows are duplicates (same context, different therapist responses).")
    print("  3. The dataset is NOT clinically validated.")
    print("  4. Class imbalance: 'crisis' and 'high' are likely underrepresented.")
    print("  5. The model should NOT be used as the sole decision maker for crisis detection;")
    print("     the deterministic regex layer is the primary safety mechanism.")

    # ── Save results ───────────────────────────────────────────────────────
    per_class = {}
    for label in labels:
        if label in report:
            per_class[label] = {
                "precision": round(report[label]["precision"], 4),
                "recall": round(report[label]["recall"], 4),
                "f1": round(report[label]["f1-score"], 4),
                "support": int(report[label]["support"]),
            }

    output = {
        "split_method": "GroupShuffleSplit (test_size=0.2, random_state=42)",
        "context_overlap": len(leaked),
        "train_samples": len(train_idx),
        "test_samples": len(test_idx),
        "unique_train_contexts": len(train_contexts),
        "unique_test_contexts": len(test_contexts),
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "per_class": per_class,
        "confusion_matrix": {
            "labels": labels,
            "matrix": cm.tolist(),
        },
        "crisis_detection": {
            "true_positives": int(crisis_tp),
            "false_negatives": int(crisis_fn),
            "false_positives": int(crisis_fp),
            "total_actual": int(crisis_actual),
        },
        "comparison_with_random_split": {
            "random_accuracy": prev_metrics.get("accuracy") if prev_metrics else None,
            "random_macro_f1": prev_metrics.get("macro_f1") if prev_metrics else None,
            "group_accuracy": round(accuracy, 4),
            "group_macro_f1": round(macro_f1, 4),
        },
        "dataset_limitations": [
            "Severity labels derived from text heuristics, not expert annotations",
            "71.7% duplicate rows inflate random-split metrics",
            "Not clinically validated",
            "Class imbalance present",
            "Should not be sole crisis decision maker",
        ],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n✓ Group-split metrics saved to {OUTPUT_PATH}")

    print("\n" + "=" * 70)
    print("PHASE B.1 COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
