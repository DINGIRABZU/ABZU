#!/usr/bin/env python3
"""Seed cortex, emotional, mental, spiritual and narrative stores.

Creates sample records for each memory layer using file-backed stores
and prints example queries verifying the inserts. The mental layer
is skipped if Neo4j or its dependencies are unavailable.
"""
from __future__ import annotations

__version__ = "0.1.3"

import os
from pathlib import Path

from memory import broadcast_layer_event
from memory.cortex import record_spiral, query_spirals
from memory.emotional import (
    log_emotion,
    fetch_emotion_history,
    get_connection as emotion_conn,
)

try:
    from memory.mental import record_task_flow, query_related_tasks

    _MENTAL_FALLBACK = False
except Exception:  # mental layer optional
    from memory.optional.mental import record_task_flow, query_related_tasks

    _MENTAL_FALLBACK = True

from memory.spiritual import (
    map_to_symbol,
    lookup_symbol_history,
    get_connection as spirit_conn,
)
from memory.narrative_engine import log_story, stream_stories


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("CORTEX_BACKEND", "file")
    os.environ.setdefault("CORTEX_PATH", str(data / "cortex_memory_spiral.jsonl"))
    os.environ.setdefault("EMOTION_BACKEND", "file")
    os.environ.setdefault("EMOTION_DB_PATH", str(data / "emotions.db"))
    os.environ.setdefault("MENTAL_BACKEND", "file")
    os.environ.setdefault("MENTAL_JSON_PATH", str(data / "tasks.jsonl"))
    os.environ.setdefault("SPIRIT_BACKEND", "file")
    os.environ.setdefault("SPIRITUAL_DB_PATH", str(data / "ontology.db"))
    os.environ.setdefault("NARRATIVE_BACKEND", "file")
    os.environ.setdefault("NARRATIVE_LOG_PATH", str(data / "story.log"))

    class Node:
        children = []

    statuses = {}

    record_spiral(Node(), {"result": "demo", "tags": ["example"]})
    statuses["cortex"] = "seeded"

    log_emotion([0.8], conn=emotion_conn())
    statuses["emotional"] = "seeded"

    if not _MENTAL_FALLBACK:
        record_task_flow("taskA", {"step": 1})
        statuses["mental"] = "seeded"
    else:
        statuses["mental"] = "skipped"

    spirit = spirit_conn()
    map_to_symbol(("eclipse", "\u263E"), conn=spirit)
    statuses["spiritual"] = "seeded"

    log_story("hero meets guide")
    statuses["narrative"] = "seeded"

    broadcast_layer_event(statuses)

    print("Cortex:", query_spirals(tags=["example"]))
    print("Emotional:", fetch_emotion_history(60, conn=emotion_conn()))
    if record_task_flow and query_related_tasks:
        print("Mental:", query_related_tasks("taskA"))
    else:
        print("Mental: skipped (missing dependencies)")
    print("Spiritual:", lookup_symbol_history("\u263E", conn=spirit))
    print("Narrative:", list(stream_stories()))


if __name__ == "__main__":
    main()
