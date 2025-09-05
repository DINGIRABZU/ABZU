#!/usr/bin/env python3
"""Populate mandatory memory layers with default records."""
from __future__ import annotations

import os
from pathlib import Path

from memory.cortex import record_spiral
from memory.emotional import log_emotion, get_connection as emotion_conn
from memory.spiritual import map_to_symbol, get_connection as spirit_conn
from memory.narrative_engine import log_story

__version__ = "0.1.0"


def main() -> None:
    """Bootstrap core layers using file-backed stores and report progress."""
    root = Path(__file__).resolve().parents[1]
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("CORTEX_BACKEND", "file")
    os.environ.setdefault("CORTEX_PATH", str(data / "cortex_memory_spiral.jsonl"))
    os.environ.setdefault("EMOTION_BACKEND", "file")
    os.environ.setdefault("EMOTION_DB_PATH", str(data / "emotions.db"))
    os.environ.setdefault("SPIRIT_BACKEND", "file")
    os.environ.setdefault("SPIRITUAL_DB_PATH", str(data / "ontology.db"))
    os.environ.setdefault("NARRATIVE_BACKEND", "file")
    os.environ.setdefault("NARRATIVE_LOG_PATH", str(data / "story.log"))

    class Node:
        children = []

    print("Bootstrapping world layers...")

    record_spiral(Node(), {"result": "init"})
    print("- Cortex layer initialized")

    log_emotion([0.0], conn=emotion_conn())
    print("- Emotional layer initialized")

    map_to_symbol(("origin", "O"), conn=spirit_conn())
    print("- Spiritual layer initialized")

    log_story("world initialized")
    print("- Narrative layer initialized")

    print("World bootstrap complete.")


if __name__ == "__main__":
    main()
