#!/usr/bin/env python3
"""Bootstrap cortex, emotional, mental, spiritual and narrative stores.

Creates sample records for each memory layer using file-backed stores,
emits readiness states from the Rust memory bundle, and prints example
queries verifying the inserts. The mental layer is reported as
``skipped`` when Neo4j or its dependencies are unavailable.
"""
from __future__ import annotations

__version__ = "0.2.0"

import os
import sys
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

    statuses: dict[str, str] = {}

    try:
        record_spiral(Node(), {"result": "demo", "tags": ["example"]})
    except Exception as exc:  # pragma: no cover - defensive logging
        statuses["cortex"] = "error"
        print(f"cortex bootstrap failed: {exc}", file=sys.stderr)
    else:
        statuses["cortex"] = "ready"

    try:
        conn = emotion_conn()
        log_emotion([0.8], conn=conn)
    except Exception as exc:  # pragma: no cover - defensive logging
        statuses["emotional"] = "error"
        print(f"emotional bootstrap failed: {exc}", file=sys.stderr)
    else:
        statuses["emotional"] = "ready"

    if not _MENTAL_FALLBACK:
        try:
            record_task_flow("taskA", {"step": 1})
        except Exception as exc:  # pragma: no cover - defensive logging
            statuses["mental"] = "error"
            print(f"mental bootstrap failed: {exc}", file=sys.stderr)
        else:
            statuses["mental"] = "ready"
    else:
        statuses["mental"] = "skipped"

    spirit = None
    try:
        spirit = spirit_conn()
        map_to_symbol(("eclipse", "\u263E"), conn=spirit)
    except Exception as exc:  # pragma: no cover - defensive logging
        statuses["spiritual"] = "error"
        print(f"spiritual bootstrap failed: {exc}", file=sys.stderr)
        spirit = None
    else:
        statuses["spiritual"] = "ready"

    try:
        log_story("hero meets guide")
    except Exception as exc:  # pragma: no cover - defensive logging
        statuses["narrative"] = "error"
        print(f"narrative bootstrap failed: {exc}", file=sys.stderr)
    else:
        statuses["narrative"] = "ready"

    broadcast_layer_event(statuses)

    print("Cortex:", query_spirals(tags=["example"]))
    print("Emotional:", fetch_emotion_history(60, conn=emotion_conn()))
    if record_task_flow and query_related_tasks:
        print("Mental:", query_related_tasks("taskA"))
    else:
        print("Mental: skipped (missing dependencies)")
    if spirit is not None:
        print("Spiritual:", lookup_symbol_history("\u263E", conn=spirit))
    else:
        print("Spiritual: error (see stderr)")
    print("Narrative:", list(stream_stories()))


if __name__ == "__main__":
    main()
