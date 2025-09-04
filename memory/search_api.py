"""Aggregate memory queries across layers with recency and source ranking."""

from __future__ import annotations

from datetime import datetime
import math
from typing import Any, Dict, List

from memory.cortex import query_spirals
from memory.emotional import fetch_emotion_history
from memory.narrative_engine import stream_stories
from memory.spiritual import lookup_symbol_history

try:  # mental layer optional
    from memory.mental import query_related_tasks
except Exception:  # pragma: no cover - dependency may be missing
    query_related_tasks = None

_DECAY_SECONDS = 86_400.0


def _recency_weight(ts: str) -> float:
    """Return exponential decay weight for ``ts``."""
    try:
        t = datetime.fromisoformat(ts)
    except Exception:
        return 1.0
    age = (datetime.utcnow() - t).total_seconds()
    return math.exp(-age / _DECAY_SECONDS)


def aggregate_search(
    query: str, *, source_weights: Dict[str, float] | None = None
) -> List[Dict[str, Any]]:
    """Return ranked matches from cortex, emotional, mental, spiritual and narrative layers."""

    q = query.lower()
    source_weights = source_weights or {}
    results: List[Dict[str, Any]] = []

    for entry in query_spirals(text=query):
        results.append(
            {
                "source": "cortex",
                "text": entry.get("decision", {}).get("result", ""),
                "timestamp": entry.get("timestamp", ""),
            }
        )

    for emo in fetch_emotion_history(100):
        if q in str(emo.vector):
            results.append(
                {
                    "source": "emotional",
                    "text": str(emo.vector),
                    "timestamp": emo.timestamp.isoformat(),
                }
            )

    if query_related_tasks:
        for task in query_related_tasks(query):
            results.append({"source": "mental", "text": task, "timestamp": ""})

    for sym in lookup_symbol_history(query):
        results.append({"source": "spiritual", "text": sym, "timestamp": ""})

    for story in stream_stories():
        if q in story.lower():
            results.append({"source": "narrative", "text": story, "timestamp": ""})

    for res in results:
        res["score"] = _recency_weight(res.get("timestamp", "")) * source_weights.get(
            res["source"], 1.0
        )

    results.sort(key=lambda r: r["score"], reverse=True)
    return results


__all__ = ["aggregate_search"]
