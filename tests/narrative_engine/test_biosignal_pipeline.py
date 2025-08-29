"""Tests for biosignal ingestion and transformation."""

from __future__ import annotations

import csv
from pathlib import Path

from memory.narrative_engine import StoryEvent

DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "biosignals"
    / "sample_biosignals.csv"
)


def load_dataset() -> list[dict[str, str]]:
    with DATA_PATH.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_ingest_biosignal_dataset() -> None:
    rows = load_dataset()
    assert len(rows) == 3
    assert set(rows[0].keys()) == {"timestamp", "heart_rate", "skin_temp", "eda"}


def test_transform_biosignals_to_event() -> None:
    row = load_dataset()[1]
    action = "elevated heart rate" if float(row["heart_rate"]) > 74 else "calm"
    event = StoryEvent(actor="subject", action=action)
    assert isinstance(event, StoryEvent)
    assert event.action == "elevated heart rate"
