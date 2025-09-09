# pydocstyle: skip-file
"""Memory subsystem package."""

from __future__ import annotations

import importlib
import sys
from typing import Dict

from agents.event_bus import emit_event
from worlds.config_registry import register_layer
from .query_memory import query_memory
from opentelemetry import trace

try:  # pragma: no cover - optional dependency
    from .chakra_registry import ChakraRegistry
except Exception:  # pragma: no cover - fallback when vector memory unavailable
    ChakraRegistry = None  # type: ignore[assignment]

__version__ = "0.1.6"

# Registered memory layers with optional fallbacks. Vector and spiral memory
# live at the package root and are included in the broadcast payload alongside
# the traditional emotional, mental, spiritual, and narrative stores.
LAYERS = (
    "cortex",
    "vector",
    "spiral",
    "emotional",
    "mental",
    "spiritual",
    "narrative",
)

_LAYER_IMPORTS = {
    "cortex": "memory.cortex",
    "vector": "vector_memory",
    "spiral": "spiral_memory",
    "emotional": "memory.emotional",
    "mental": "memory.mental",
    "spiritual": "memory.spiritual",
    "narrative": "memory.narrative_engine",
}

_LAYER_STATUSES: Dict[str, str] = {}
_tracer = trace.get_tracer(__name__)


def _load_layer(layer: str) -> str:
    """Import ``layer`` and load optional fallback on ``ModuleNotFoundError``."""

    with _tracer.start_as_current_span("memory.load_layer") as span:
        span.set_attribute("memory.layer", layer)
        module_path = _LAYER_IMPORTS[layer]
        try:  # pragma: no cover - import may fail
            module = importlib.import_module(module_path)
            status = "ready"
        except ModuleNotFoundError:  # pragma: no cover - logged elsewhere
            optional_path = f"memory.optional.{module_path.rsplit('.', 1)[-1]}"
            try:
                module = importlib.import_module(optional_path)
                status = "skipped"
            except ModuleNotFoundError:
                module = None
                status = "error"
        except Exception:  # pragma: no cover - unexpected import error
            module = None
            status = "error"
        if module is not None:
            sys.modules[module_path] = module
        _LAYER_STATUSES[layer] = status
        span.set_attribute("memory.load_status", status)
        return status


for _layer in LAYERS:
    register_layer(_layer)
    _load_layer(_layer)


def broadcast_layer_event(statuses: Dict[str, str]) -> Dict[str, str]:
    """Emit a single initialization event for all memory layers.

    ``statuses`` maps layer names to their corresponding status strings. The
    mapping may omit entries; missing values are populated using the latest
    import results so callers can submit only overrides. Fallback modules are
    loaded automatically during import.
    """

    with _tracer.start_as_current_span("memory.broadcast_layer_event") as span:
        for layer in LAYERS:
            if statuses.get(layer) != "ready":
                statuses[layer] = _LAYER_STATUSES.get(layer, "error")
        span.set_attribute("memory.layers", ",".join(LAYERS))

        emit_event(
            "memory",
            "layer_init",
            {"layers": {layer: statuses.get(layer, "unknown") for layer in LAYERS}},
        )
        return statuses


# Emit a consolidated status event once all layers have been attempted.
broadcast_layer_event(_LAYER_STATUSES)


LAYER_STATUSES = _LAYER_STATUSES

__all__ = [
    "broadcast_layer_event",
    "query_memory",
    "LAYERS",
    "LAYER_STATUSES",
    "ChakraRegistry",
]
