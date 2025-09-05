"""Facade for coordinated memory layer initialization and querying."""

from __future__ import annotations

from dataclasses import dataclass, field
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

        try:
            from . import cortex as cortex_layer

            self.cortex = cortex_layer
            statuses["cortex"] = "ready"
        except Exception:  # pragma: no cover - import failure logged elsewhere
            statuses["cortex"] = "error"

        try:
            from . import emotional as emotional_layer

            self.emotional = emotional_layer
            statuses["emotional"] = "ready"
        except Exception:  # pragma: no cover
            statuses["emotional"] = "error"

        try:
            from . import mental as mental_layer

            self.mental = mental_layer
            statuses["mental"] = "ready"
        except Exception:  # mental layer optional
            from .optional import mental as mental_layer

            self.mental = mental_layer
            statuses["mental"] = "defaulted"

        try:
            from . import spiritual as spiritual_layer

            self.spiritual = spiritual_layer
            statuses["spiritual"] = "ready"
        except Exception:  # pragma: no cover
            statuses["spiritual"] = "error"

        try:
            from . import narrative_engine as narrative_layer

            self.narrative = narrative_layer
            statuses["narrative"] = "ready"
        except Exception:  # pragma: no cover
            statuses["narrative"] = "error"

        broadcast_layer_event(statuses)
        self.statuses = statuses
        return statuses

    def query(self, text: str) -> Dict[str, Any]:
        """Delegate to :func:`query_memory` to aggregate layer results."""
        return query_memory(text)


__all__ = ["MemoryBundle"]
