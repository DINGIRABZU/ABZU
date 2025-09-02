"""Ingest biosignals jsonl module for scripts."""

from __future__ import annotations

import json
from pathlib import Path

from data.biosignals import DATASET_HASHES, hash_file
from memory import narrative_engine

__version__ = "0.2.0"

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "biosignals"


def ingest_file(jsonl_path: Path) -> None:
    """Read ``jsonl_path`` and store each row as a structured event."""
    expected = DATASET_HASHES.get(jsonl_path.name)
    actual = hash_file(jsonl_path)
    if expected and actual != expected:
        raise ValueError(f"hash mismatch for {jsonl_path.name}")

    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            action = "elevated heart rate" if float(row["heart_rate"]) > 74 else "calm"
            event = {
                "time": row["timestamp"],
                "agent_id": "sensor",
                "event_type": "biosignal",
                "payload": {
                    "action": action,
                    "heart_rate": float(row["heart_rate"]),
                    "skin_temp": float(row["skin_temp"]),
                    "eda": float(row["eda"]),
                },
            }
            narrative_engine.log_event(event)


def ingest_directory(directory: Path = DATA_DIR) -> None:
    """Process all JSONL files in ``directory``."""
    for jsonl_path in directory.glob("*.jsonl"):
        ingest_file(jsonl_path)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    ingest_directory()
