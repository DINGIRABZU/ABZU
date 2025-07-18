from __future__ import annotations

"""Train and apply a simple emotion classifier using scikit-learn."""

from pathlib import Path
from typing import Tuple, Iterable, List, Dict

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.base import ClassifierMixin
import joblib

from INANNA_AI import listening_engine
import emotional_state
import corpus_memory_logging

MODEL_PATH = Path("models/emotion_clf.joblib")
_MODEL: ClassifierMixin | None = None


def _entry_to_sample(entry: Dict[str, float | str]) -> Tuple[np.ndarray, str] | None:
    """Convert a history entry to (features, label)."""
    try:
        pitch = float(entry["pitch"])
        tempo = float(entry["tempo"])
        emotion = str(entry["emotion"])
    except Exception:
        return None
    return np.array([pitch, tempo], dtype=float), emotion


def collect_samples_from_microphone(
    count: int = 20, duration: float = 0.5, sr: int = 44100
) -> Tuple[np.ndarray, np.ndarray]:
    """Capture ``count`` microphone chunks and return features and labels."""
    feats: List[np.ndarray] = []
    labels: List[str] = []
    for _ in range(count):
        _, info = listening_engine.analyze_audio(duration, sr)
        pitch = float(info.get("pitch", 0.0))
        tempo = float(info.get("tempo", 0.0))
        emotion = emotional_state.get_last_emotion() or str(info.get("emotion", "neutral"))
        feats.append(np.array([pitch, tempo], dtype=float))
        labels.append(emotion)
    return np.vstack(feats), np.array(labels, dtype=str)


def load_recent_samples(limit: int = 50) -> Tuple[np.ndarray, np.ndarray]:
    """Return recent (features, labels) from interaction history."""
    entries = corpus_memory_logging.load_interactions(limit)
    feats: List[np.ndarray] = []
    labels: List[str] = []
    for e in entries:
        sample = _entry_to_sample(e)
        if sample is None:
            continue
        f, lab = sample
        feats.append(f)
        labels.append(lab)
    if feats:
        return np.vstack(feats), np.array(labels, dtype=str)
    return np.empty((0, 2)), np.array([], dtype=str)


def train(limit: int = 50) -> ClassifierMixin:
    """Train a RandomForest on recent history and save to :data:`MODEL_PATH`."""
    X, y = load_recent_samples(limit)
    if len(y) < 2:
        raise RuntimeError("not enough training data")
    clf = RandomForestClassifier(n_estimators=50, random_state=0)
    clf.fit(X, y)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    global _MODEL
    _MODEL = clf
    return clf


def train_from_arrays(X: np.ndarray, y: Iterable[str]) -> ClassifierMixin:
    """Train a classifier from ``X`` and ``y`` arrays and save the model."""
    clf = RandomForestClassifier(n_estimators=50, random_state=0)
    clf.fit(X, list(y))
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    global _MODEL
    _MODEL = clf
    return clf


def _load_model() -> ClassifierMixin:
    """Return the trained model loading from disk if needed."""
    global _MODEL
    if _MODEL is None:
        if not MODEL_PATH.is_file():
            raise RuntimeError("emotion classifier model not trained")
        _MODEL = joblib.load(MODEL_PATH)
    return _MODEL


def predict_emotion(features: Dict[str, float]) -> str:
    """Predict an emotion label for ``features``."""
    model = _load_model()
    pitch = float(features.get("pitch", 0.0))
    tempo = float(features.get("tempo", 0.0))
    X = np.array([[pitch, tempo]], dtype=float)
    return str(model.predict(X)[0])


__all__ = [
    "train",
    "train_from_arrays",
    "predict_emotion",
    "load_recent_samples",
    "collect_samples_from_microphone",
    "MODEL_PATH",
]
