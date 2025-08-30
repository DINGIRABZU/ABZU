"""Validate biosignal action transformation during ingestion."""

from __future__ import annotations

from pathlib import Path

import pytest

from memory import narrative_engine
from scripts.ingest_biosignals import ingest_file

__version__ = "0.1.0"

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "biosignals"


def test_ingest_file_transforms_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    csv_path = DATA_DIR / "sample_biosignals.csv"
    logged: list[str] = []
    monkeypatch.setattr(narrative_engine, "log_story", lambda text: logged.append(text))
    ingest_file(csv_path)
    assert logged == ["calm", "elevated heart rate", "calm"]
