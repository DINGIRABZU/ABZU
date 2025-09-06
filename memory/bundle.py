"""Facade for coordinated memory layer initialization and querying."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Any, Dict

from . import LAYERS, _LAYER_IMPORTS, broadcast_layer_event, query_memory

__version__ = "0.1.1"


@dataclass
class MemoryBundle:
    """Bundle that instantiates memory layers and aggregates queries."""

    cortex: Any | None = None
    emotional: Any | None = None
    mental: Any | None = None
    spiritual: Any | None = None
    narrative: Any | None = None
    statuses: Dict[str, str] = field(default_factory=dict)

    def initialize(self) -> Dict[str, str]:
        """Instantiate memory layers and emit a consolidated status event."""
        statuses: Dict[str, str] = {}

        for layer in LAYERS:
            module_path = _LAYER_IMPORTS[layer]
            module = import_module(module_path)
            setattr(self, layer, module)
            name = getattr(module, "__name__", "")
            statuses[layer] = (
                "defaulted" if name.startswith("memory.optional.") else "ready"
            )

        broadcast_layer_event(statuses)
        self.statuses = statuses
        return statuses

    def query(self, text: str) -> Dict[str, Any]:
        """Delegate to :func:`query_memory` to aggregate layer results."""
        return query_memory(text)


__all__ = ["MemoryBundle"]
