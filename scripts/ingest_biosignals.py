"""Ingest biosignal CSV files into the narrative engine."""

from __future__ import annotations

import csv
from pathlib import Path

from data.biosignals import DATASET_HASHES, hash_file
from memory.narrative_engine import StoryEvent, log_story

__version__ = "0.2.0"

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "biosignals"


def ingest_file(csv_path: Path) -> None:
    """Read ``csv_path`` and log story events derived from its rows."""
    expected = DATASET_HASHES.get(csv_path.name)
    actual = hash_file(csv_path)
    if expected and actual != expected:
        raise ValueError(f"hash mismatch for {csv_path.name}")

    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            action = "elevated heart rate" if float(row["heart_rate"]) > 74 else "calm"
            event = StoryEvent(actor="subject", action=action)
            log_story(event.action)


def ingest_directory(directory: Path = DATA_DIR) -> None:
    """Process all CSV files in ``directory``."""
    for csv_path in directory.glob("*.csv"):
        ingest_file(csv_path)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    ingest_directory()
