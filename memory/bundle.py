"""Facade for coordinated memory layer initialization and querying."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Any, Dict

from . import broadcast_layer_event, query_memory


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

        module_map = {
            "cortex": "memory.cortex",
            "emotional": "memory.emotional",
            "mental": "memory.mental",
            "spiritual": "memory.spiritual",
            "narrative": "memory.narrative_engine",
        }

        for layer, module_path in module_map.items():
            attr = layer
            try:
                module = import_module(module_path)
                setattr(self, attr, module)
                statuses[layer] = "ready"
            except Exception:  # pragma: no cover - import failure logged elsewhere
                optional_path = f"memory.optional.{module_path.split('.')[-1]}"
                try:
                    module = import_module(optional_path)
                    setattr(self, attr, module)
                    statuses[layer] = "defaulted"
                except Exception:  # pragma: no cover - optional missing
                    setattr(self, attr, None)
                    statuses[layer] = "error"

        broadcast_layer_event(statuses)
        self.statuses = statuses
        return statuses

    def query(self, text: str) -> Dict[str, Any]:
        """Delegate to :func:`query_memory` to aggregate layer results."""
        return query_memory(text)


__all__ = ["MemoryBundle"]
