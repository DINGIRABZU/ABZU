#!/usr/bin/env python3
"""Ingest sample events into each memory layer and verify retrieval."""
from __future__ import annotations

import os
from pathlib import Path

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

    # Ingest sample events
    record_spiral(Node(), {"result": "sample", "tags": ["demo"]})
    log_emotion([0.42], conn=emotion_conn())
    if record_task_flow and query_related_tasks:
        record_task_flow("taskB", {"step": 1})
    spirit = spirit_conn()
    map_to_symbol(("sunrise", "\u2600"), conn=spirit)
    log_story("protagonist awakens")

    # Verify retrieval from each layer
    assert query_spirals(tags=["demo"]), "cortex retrieval failed"
    assert fetch_emotion_history(60, conn=emotion_conn()), "emotional retrieval failed"
    if query_related_tasks:
        assert query_related_tasks("taskB"), "mental retrieval failed"
    assert lookup_symbol_history("\u2600", conn=spirit), "spiritual retrieval failed"
    assert list(stream_stories()), "narrative retrieval failed"
    print("All layers ingested and verified")


if __name__ == "__main__":
    main()
