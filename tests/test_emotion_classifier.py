"""Tests for emotion classifier."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.conftest import allow_test

allow_test(__file__)

sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("sounddevice", types.ModuleType("sounddevice"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))


class _DummyClassifierMixin:
    """Minimal stand-in for :mod:`sklearn.base` mixins."""


class _DummyRandomForestClassifier:
    """Tiny drop-in replacement for :class:`RandomForestClassifier`."""

    def __init__(self, n_estimators: int = 50, random_state: object | None = None):
        self.random_state = random_state or np.random.RandomState()
        self._mapping: dict[tuple[float, float], str] = {}
        self._default: str | None = None

    def fit(self, X, y):
        self._mapping = {tuple(row): label for row, label in zip(X, y)}
        self._default = next(iter(self._mapping.values()), None)
        return self

    def predict(self, X):
        return [self._mapping.get(tuple(row), self._default) for row in X]


sklearn = types.ModuleType("sklearn")
ensemble = types.ModuleType("ensemble")
ensemble.RandomForestClassifier = _DummyRandomForestClassifier
base = types.ModuleType("base")
base.ClassifierMixin = _DummyClassifierMixin
sklearn.ensemble = ensemble
sklearn.base = base
sys.modules.setdefault("sklearn", sklearn)
sys.modules.setdefault("sklearn.ensemble", ensemble)
sys.modules.setdefault("sklearn.base", base)

from ml import emotion_classifier as ec


def test_train_and_predict(tmp_path, monkeypatch):
    model_path = tmp_path / "model.joblib"
    monkeypatch.setattr(ec, "MODEL_PATH", model_path)

    X = np.array(
        [
            [100.0, 80.0],
            [350.0, 130.0],
            [200.0, 100.0],
        ]
    )
    y = np.array(["calm", "stress", "neutral"])

    ec.train_from_arrays(X, y)
    assert model_path.exists()

    ec._MODEL = None
    pred = ec.predict_emotion({"pitch": 350.0, "tempo": 130.0})
    assert pred == "stress"
