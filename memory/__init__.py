# pydocstyle: skip-file
"""Memory subsystem package."""

from __future__ import annotations

import importlib
from typing import Dict

from agents.event_bus import emit_event
from worlds.config_registry import register_layer
from .query_memory import query_memory

__version__ = "0.1.3"

LAYERS = ("cortex", "emotional", "mental", "spiritual", "narrative")

_LAYER_IMPORTS = {
    "cortex": "memory.cortex",
    "emotional": "memory.emotional",
    "mental": "memory.mental",
    "spiritual": "memory.spiritual",
    "narrative": "memory.narrative_engine",
}

for _layer in LAYERS:
    register_layer(_layer)


def broadcast_layer_event(statuses: Dict[str, str]) -> Dict[str, str]:
    """Emit a single initialization event for all memory layers.

    ``statuses`` maps layer names to their corresponding status strings.
    Missing entries trigger an import attempt. When importing a layer fails,
    a no-op fallback from ``memory.optional`` is substituted and the status is
    updated to ``"defaulted"``. If both imports fail the status becomes
    ``"error"``.
    """

    for layer, module_path in _LAYER_IMPORTS.items():
        if statuses.get(layer) == "ready":
            continue
        try:  # pragma: no cover - import may fail
            importlib.import_module(module_path)
            statuses[layer] = "ready"
        except Exception:  # pragma: no cover - logged elsewhere
            optional_path = f"memory.optional.{module_path.rsplit('.', 1)[-1]}"
            try:
                importlib.import_module(optional_path)
                statuses[layer] = "defaulted"
            except Exception:
                statuses[layer] = "error"

    emit_event(
        "memory",
        "layer_init",
        {"layers": {layer: statuses.get(layer, "unknown") for layer in LAYERS}},
    )
    return statuses


__all__ = ["broadcast_layer_event", "query_memory", "LAYERS"]
