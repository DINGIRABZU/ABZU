#!/usr/bin/env python3
"""Seed cortex, emotional, mental, spiritual and narrative stores.

Creates sample records for each memory layer using file-backed stores
and prints example queries verifying the inserts. The mental layer
is skipped if Neo4j or its dependencies are unavailable.
"""
from __future__ import annotations

__version__ = "0.1.1"

import os
from pathlib import Path

from memory import publish_layer_event
from memory.cortex import record_spiral, query_spirals
from memory.emotional import (
    log_emotion,
    fetch_emotion_history,
    get_connection as emotion_conn,
)

try:
    from memory.mental import record_task_flow, query_related_tasks
except Exception:  # mental layer optional
    record_task_flow = query_related_tasks = None

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

    record_spiral(Node(), {"result": "demo", "tags": ["example"]})
    publish_layer_event("cortex", "seeded")

    log_emotion([0.8], conn=emotion_conn())
    publish_layer_event("emotional", "seeded")

    if record_task_flow and query_related_tasks:
        record_task_flow("taskA", {"step": 1})
        publish_layer_event("mental", "seeded")
    else:
        publish_layer_event("mental", "skipped")

    spirit = spirit_conn()
    map_to_symbol(("eclipse", "\u263E"), conn=spirit)
    publish_layer_event("spiritual", "seeded")

    log_story("hero meets guide")
    publish_layer_event("narrative", "seeded")

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
