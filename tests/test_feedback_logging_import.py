"""Regression tests for the feedback_logging compatibility wrapper."""

from __future__ import annotations

from pathlib import Path

import importlib

import feedback_logging as fl
from pytest import MonkeyPatch


def test_feedback_logging_shim(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(fl, "LOG_FILE", tmp_path / "log.json")
    mod = importlib.reload(fl)
    assert isinstance(mod.NOVELTY_THRESHOLD, float)
    mod.append_feedback({"foo": "bar"})
    data = mod.load_feedback()
    assert data and data[0]["foo"] == "bar"
