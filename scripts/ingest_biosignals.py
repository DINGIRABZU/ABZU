"""Ingest biosignal CSV files into the narrative engine."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List

from data.biosignals import DATASET_HASHES, hash_file
from memory.narrative_engine import StoryEvent, compose_multitrack_story, log_story

__version__ = "0.2.1"

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "biosignals"


def ingest_file(csv_path: Path) -> List[StoryEvent]:
    """Read ``csv_path`` and log story events derived from its rows."""
    expected = DATASET_HASHES.get(csv_path.name)
    actual = hash_file(csv_path)
    if expected and actual != expected:
        raise ValueError(f"hash mismatch for {csv_path.name}")

    events: List[StoryEvent] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            action = "elevated heart rate" if float(row["heart_rate"]) > 74 else "calm"
            event = StoryEvent(actor="subject", action=action)
            log_story(event.action)
            events.append(event)
    return events


def ingest_directory(directory: Path = DATA_DIR) -> Dict[str, Any]:
    """Process all CSV files in ``directory`` and compose a multitrack story."""
    events: List[StoryEvent] = []
    for csv_path in directory.glob("*.csv"):
        events.extend(ingest_file(csv_path))
    return compose_multitrack_story(events)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    tracks = ingest_directory()
    print(tracks)
