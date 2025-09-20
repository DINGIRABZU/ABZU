#!/usr/bin/env python3
"""Verify memory layers respond with ready bootstrap data.

Runs minimal queries against each layer. Raises ``RuntimeError``
if any layer is empty or unavailable, mirroring the ``ready``
state emitted by the Rust bundle. Used to guard Albedo
initialisation before persona modules load.
"""
from __future__ import annotations

from pathlib import Path
import sys
import os

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DATA_DIR = ROOT / "data"
os.environ.setdefault("CORTEX_PATH", str(DATA_DIR / "cortex.jsonl"))
os.environ.setdefault("EMOTION_DB_PATH", str(DATA_DIR / "emotions.db"))
os.environ.setdefault("MENTAL_JSON_PATH", str(DATA_DIR / "tasks.jsonl"))
os.environ.setdefault("SPIRITUAL_DB_PATH", str(DATA_DIR / "ontology.db"))
os.environ.setdefault("NARRATIVE_LOG_PATH", str(DATA_DIR / "story.log"))

__version__ = "0.1.2"

from memory.cortex import query_spirals
from memory.emotional import fetch_emotion_history, get_connection as emotion_conn

try:
    from memory.mental import query_related_tasks

    _MENTAL_FALLBACK = False
except Exception:  # mental layer optional
    from memory.optional.mental import query_related_tasks

    _MENTAL_FALLBACK = True
from memory.spiritual import lookup_symbol_history, get_connection as spirit_conn
from memory.narrative_engine import stream_stories


def verify_memory_layers() -> None:
    """Ensure each memory layer returns data."""
    if not query_spirals(tags=["example"]):
        raise RuntimeError("cortex layer empty")

    if not fetch_emotion_history(60, conn=emotion_conn()):
        raise RuntimeError("emotional layer empty")

    if not _MENTAL_FALLBACK and not query_related_tasks("taskA"):
        raise RuntimeError("mental layer empty")

    if not lookup_symbol_history("\u263E", conn=spirit_conn()):
        raise RuntimeError("spiritual layer empty")

    if not list(stream_stories()):
        raise RuntimeError("narrative layer empty")


if __name__ == "__main__":  # pragma: no cover - manual check
    verify_memory_layers()
    print("memory checks passed")
