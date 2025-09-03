# pydocstyle: skip-file
"""Unified memory search across multiple subsystems."""

from __future__ import annotations

__version__ = "0.2.0"

import json
import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Optional

import spiral_memory
import vector_memory
from vector_memory import cosine_similarity, embed_text
from memory import cortex

logger = logging.getLogger(__name__)

_DECAY_SECONDS = 86_400.0


def _recency_weight(ts: str) -> float:
    """Return exponential decay weight for ``ts``."""
    try:
        t = datetime.fromisoformat(ts)
    except Exception:
        return 1.0
    age = (datetime.utcnow() - t).total_seconds()
    return math.exp(-age / _DECAY_SECONDS)


def query_all(
    text: str,
    *,
    k: int = 5,
    filters: Optional[Dict[str, Any]] = None,
    scoring: str = "hybrid",
    source_weights: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """Aggregate matches from cortex, spiral and vector memories.

    ``filters`` apply semantic filtering on the returned items. ``scoring``
    controls how similarity and recency are combined and ``source_weights``
    allows boosting particular memory subsystems.
    """

    needle = text.lower()
    qvec = embed_text(text)
    source_weights = source_weights or {}
    index: Dict[str, Dict[str, Any]] = {}

    def passes(res: Dict[str, Any]) -> bool:
        if not filters:
            return True
        for key, val in filters.items():
            if res.get(key) != val:
                return False
        return True

    def score_entry(sim: float, ts: str, source: str) -> float:
        rec = _recency_weight(ts)
        if scoring == "similarity":
            base = sim
        elif scoring == "recency":
            base = rec
        else:
            base = sim * rec
        return base * source_weights.get(source, 1.0)

    def add(res: Dict[str, Any]) -> None:
        if not passes(res):
            return
        key = res["text"].lower()
        cur = index.get(key)
        if cur is None or res.get("score", 0.0) > cur.get("score", 0.0):
            index[key] = res

    try:
        for entry in cortex.query_spirals():
            state = entry.get("state", "")
            decision = json.dumps(entry.get("decision", ""), ensure_ascii=False)
            hay = f"{state} {decision}".lower()
            if needle in hay:
                ts = entry.get("timestamp", "")
                text_val = state or decision
                sim = cosine_similarity(embed_text(text_val), qvec)
                add(
                    {
                        "source": "cortex",
                        "text": text_val,
                        "timestamp": ts,
                        "score": score_entry(sim, ts, "cortex"),
                    }
                )
    except Exception as exc:  # pragma: no cover - just logging
        logger.warning("cortex query failed: %s", exc)

    try:
        events = spiral_memory.DEFAULT_MEMORY._load_events()  # type: ignore[attr-defined]
        for event, _glyph, _phrase in events:
            if needle in event.lower():
                sim = cosine_similarity(embed_text(event), qvec)
                add(
                    {
                        "source": "spiral",
                        "text": event,
                        "timestamp": "",
                        "score": score_entry(sim, "", "spiral"),
                    }
                )
    except Exception as exc:  # pragma: no cover - just logging
        logger.warning("spiral query failed: %s", exc)

    try:
        for hit in vector_memory.search(text, k=k, scoring=scoring):
            ts = hit.get("timestamp", "")
            add(
                {
                    "source": "vector",
                    "text": hit.get("text", ""),
                    "timestamp": ts,
                    "score": hit.get("score", 0.0) * source_weights.get("vector", 1.0),
                }
            )
    except Exception as exc:  # pragma: no cover - just logging
        logger.warning("vector search failed: %s", exc)

    results = sorted(index.values(), key=lambda r: r.get("score", 0.0), reverse=True)
    return results[:k]


__all__ = ["query_all"]
