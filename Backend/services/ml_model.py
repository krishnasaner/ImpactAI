"""
ImpactAI — ML severity classifier service.

A lightweight, high-performance TF-IDF + Logistic Regression pipeline
that classifies mental health distress severity:
    low / medium / high / crisis

At runtime, this module loads the artifacts once and exposes thread-safe
prediction and metadata inspection functions.
"""

import json
import logging
import pickle
import threading
from pathlib import Path
from typing import Optional, Tuple

from config import ML_MODEL_PATH, ML_VECTORIZER_PATH

logger = logging.getLogger(__name__)

_vectorizer = None
_model = None
_metrics = None
_loaded = False
_lock = threading.Lock()

METRICS_PATH = ML_MODEL_PATH.parent / "model_metrics.json"


def _load_model() -> None:
    global _vectorizer, _model, _metrics, _loaded
    if _loaded:
        return

    with _lock:
        if _loaded:
            return

        if ML_MODEL_PATH.exists() and ML_VECTORIZER_PATH.exists():
            try:
                with open(ML_VECTORIZER_PATH, "rb") as f:
                    _vectorizer = pickle.load(f)
                with open(ML_MODEL_PATH, "rb") as f:
                    _model = pickle.load(f)
                logger.info("ML severity model and vectorizer loaded successfully.")

                if METRICS_PATH.exists():
                    try:
                        with open(METRICS_PATH, "r") as mf:
                            _metrics = json.load(mf)
                    except Exception as err:
                        logger.warning("Could not read model_metrics.json: %s", err)

            except Exception as exc:
                logger.error("Failed to load ML artifacts: %s", exc)
                _vectorizer = None
                _model = None
        else:
            logger.warning(
                "No trained ML model found at %s. Run Backend/scripts/evaluate_and_train.py",
                ML_MODEL_PATH,
            )

        _loaded = True


def is_model_available() -> bool:
    _load_model()
    return _model is not None and _vectorizer is not None


def predict_severity(text: str) -> Tuple[str, float]:
    """
    Return (label, confidence) for the given input text.
    Handles empty text and falls back safely to ("low", 0.0) if model is unavailable.
    """
    _load_model()
    if _model is None or _vectorizer is None:
        return "low", 0.0

    cleaned = (text or "").strip()
    if not cleaned:
        return "low", 1.0

    try:
        X = _vectorizer.transform([cleaned])
        label = _model.predict(X)[0]
        probas = _model.predict_proba(X)[0]
        confidence = float(max(probas))
        return str(label), round(confidence, 4)
    except Exception as exc:
        logger.warning("Inference error in predict_severity: %s", exc)
        return "low", 0.0


def get_model_info() -> Optional[dict]:
    """Return model type, classes, and evaluation metrics."""
    _load_model()
    if _model is None:
        return None

    classes_ = list(_model.classes_) if hasattr(_model, "classes_") else []
    info = {
        "model_type": type(_model).__name__,
        "classes": classes_,
        "vectorizer_features": (
            _vectorizer.max_features
            if hasattr(_vectorizer, "max_features")
            else None
        ),
    }
    if _metrics:
        info["metrics"] = _metrics.get("evaluation")
        info["version"] = _metrics.get("model_version", "2.1.0")
    return info
