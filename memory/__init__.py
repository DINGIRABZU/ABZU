# pydocstyle: skip-file
"""Memory subsystem package."""

from __future__ import annotations

from typing import Dict

from agents.event_bus import emit_event
from worlds.config_registry import register_layer
from .query_memory import query_memory

__version__ = "0.1.3"

LAYERS = ("cortex", "emotional", "mental", "spiritual", "narrative")

for _layer in LAYERS:
    register_layer(_layer)


def broadcast_layer_event(statuses: Dict[str, str]) -> None:
    """Emit a single initialization event for all memory layers.

    ``statuses`` maps layer names to their corresponding status strings. Layers
    missing from the mapping default to ``"unknown"``.
    """

    emit_event(
        "memory",
        "layer_init",
        {"layers": {layer: statuses.get(layer, "unknown") for layer in LAYERS}},
    )


__all__ = ["broadcast_layer_event", "query_memory", "LAYERS"]
