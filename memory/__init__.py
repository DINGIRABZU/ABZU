# pydocstyle: skip-file
"""Memory subsystem package."""

from __future__ import annotations

from typing import Any, Dict

from agents.event_bus import emit_event
from memory.cortex import query_spirals
from spiral_memory import spiral_recall
from vector_memory import query_vectors

__version__ = "0.1.3"

LAYERS = ("cortex", "emotional", "mental", "spiritual", "narrative")


def broadcast_layer_event(statuses: Dict[str, str]) -> None:
    """Emit initialization ``statuses`` for all memory layers via the event bus.

    ``statuses`` maps layer names to their corresponding status strings.
    Layers missing from the mapping default to ``"unknown"``.
    """

    for layer in LAYERS:
        emit_event(
            "memory",
            "layer_init",
            {"layer": layer, "status": statuses.get(layer, "unknown")},
        )


def query_memory(query: str) -> Dict[str, Any]:
    """Return aggregated results across cortex, vector, and spiral memory."""

    return {
        "cortex": query_spirals(text=query),
        "vector": query_vectors(filter={"text": query}),
        "spiral": spiral_recall(query),
    }


__all__ = ["broadcast_layer_event", "query_memory", "LAYERS"]
