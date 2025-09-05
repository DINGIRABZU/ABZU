"""Aggregated memory queries across cortex, vector, and spiral stores."""

from __future__ import annotations

from typing import Any, Dict

from .cortex import query_spirals
from spiral_memory import spiral_recall
from vector_memory import query_vectors


def query_memory(query: str) -> Dict[str, Any]:
    """Return aggregated results across cortex, vector, and spiral memory."""

    return {
        "cortex": query_spirals(text=query),
        "vector": query_vectors(filter={"text": query}),
        "spiral": spiral_recall(query),
    }


__all__ = ["query_memory"]
