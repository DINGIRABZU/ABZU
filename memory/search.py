"""Unified memory search across multiple subsystems."""

from __future__ import annotations

import json
import math
from datetime import datetime
from typing import Any, Dict, List

import spiral_memory
import vector_memory
from memory import cortex

_DECAY_SECONDS = 86_400.0


def _recency_weight(ts: str) -> float:
    """Return exponential decay weight for ``ts``."""
    try:
        t = datetime.fromisoformat(ts)
    except Exception:
        return 1.0
    age = (datetime.utcnow() - t).total_seconds()
    return math.exp(-age / _DECAY_SECONDS)


def query_all(text: str) -> List[Dict[str, Any]]:
    """Aggregate matches from cortex, spiral and vector memories."""
    needle = text.lower()
    results: List[Dict[str, Any]] = []

    try:
        for entry in cortex.query_spirals():
            state = entry.get("state", "")
            decision = json.dumps(entry.get("decision", ""), ensure_ascii=False)
            hay = f"{state} {decision}".lower()
            if needle in hay:
                ts = entry.get("timestamp", "")
                results.append(
                    {
                        "source": "cortex",
                        "text": state or decision,
                        "timestamp": ts,
                        "weight": _recency_weight(ts),
                    }
                )
    except Exception:
        pass

    try:
        events = spiral_memory.DEFAULT_MEMORY._load_events()  # type: ignore[attr-defined]
        for event, _glyph, _phrase in events:
            if needle in event.lower():
                results.append(
                    {
                        "source": "spiral",
                        "text": event,
                        "timestamp": "",
                        "weight": 1.0,
                    }
                )
    except Exception:
        pass

    try:
        for hit in vector_memory.search(text, k=5):
            ts = hit.get("timestamp", "")
            results.append(
                {
                    "source": "vector",
                    "text": hit.get("text", ""),
                    "timestamp": ts,
                    "weight": _recency_weight(ts),
                }
            )
    except Exception:
        pass

    results.sort(key=lambda r: r.get("weight", 0.0), reverse=True)
    return results


__all__ = ["query_all"]
