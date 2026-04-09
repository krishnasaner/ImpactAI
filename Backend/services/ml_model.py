"""
ImpactAI — ML severity classifier.

A lightweight TF‑IDF + Logistic Regression pipeline that predicts
the mental‑health severity of a user message:
    low / medium / high / crisis

The model is trained via  scripts/train_model.py  and persisted
as two pickles (vectorizer + classifier) under  ml_models/.

At runtime, this module loads the artefacts (if they exist) and
exposes a single  predict_severity(text)  function.
"""

import pickle
from pathlib import Path
from typing import Tuple, Optional

from config import ML_MODEL_PATH, ML_VECTORIZER_PATH

_vectorizer = None
_model = None
_loaded = False


def _load_model() -> None:
    global _vectorizer, _model, _loaded
    if _loaded:
        return
    if ML_MODEL_PATH.exists() and ML_VECTORIZER_PATH.exists():
        with open(ML_VECTORIZER_PATH, "rb") as f:
            _vectorizer = pickle.load(f)
        with open(ML_MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
        print("[ML] Severity model loaded successfully.")
    else:
        print(
            "[ML] No trained model found. "
            "Run  python scripts/train_model.py  to create one."
        )
    _loaded = True


def is_model_available() -> bool:
    _load_model()
    return _model is not None and _vectorizer is not None


def predict_severity(text: str) -> Tuple[str, float]:
    """
    Return (label, confidence) for the given text.
    Falls back to ("low", 0.0) when no model is loaded.
    """
    _load_model()
    if _model is None or _vectorizer is None:
        return "low", 0.0

    X = _vectorizer.transform([text])
    label = _model.predict(X)[0]
    probas = _model.predict_proba(X)[0]
    confidence = float(max(probas))
    return str(label), confidence


def get_model_info() -> Optional[dict]:
    """Return basic metadata about the loaded model."""
    _load_model()
    if _model is None:
        return None
    classes_ = list(_model.classes_) if hasattr(_model, "classes_") else []
    return {
        "model_type": type(_model).__name__,
        "classes": classes_,
        "vectorizer_features": (
            _vectorizer.max_features
            if hasattr(_vectorizer, "max_features")
            else None
        ),
    }
