# pydocstyle: skip-file
"""Memory subsystem package."""

from __future__ import annotations

from typing import Any, Dict

from agents.event_bus import emit_event
from memory.cortex import query_spirals
from spiral_memory import spiral_recall
from vector_memory import query_vectors

__version__ = "0.1.2"


def publish_layer_event(layer: str, status: str) -> None:
    """Emit initialization ``status`` for memory ``layer`` via the event bus."""

    emit_event("memory", "layer_init", {"layer": layer, "status": status})


def query_memory(query: str) -> Dict[str, Any]:
    """Return aggregated results across cortex, vector, and spiral memory."""

    return {
        "cortex": query_spirals(text=query),
        "vector": query_vectors(filter={"text": query}),
        "spiral": spiral_recall(query),
    }


__all__ = ["publish_layer_event", "query_memory"]
