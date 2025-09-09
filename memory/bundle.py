"""Facade for coordinated memory layer initialization and querying."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from contextlib import nullcontext
from typing import Any, Dict

from . import LAYERS, _LAYER_IMPORTS, broadcast_layer_event, query_memory

try:  # pragma: no cover - optional dependency
    from opentelemetry import trace

    _TRACER = trace.get_tracer(__name__)
except ImportError:  # pragma: no cover - dependency missing

    class _NoOpTracer:
        def start_as_current_span(self, *args: Any, **kwargs: Any):  # noqa: ANN001
            return nullcontext()

    _TRACER = _NoOpTracer()

__version__ = "0.1.4"


@dataclass
class MemoryBundle:
    """Bundle that instantiates memory layers and aggregates queries."""

    cortex: Any | None = None
    vector: Any | None = None
    spiral: Any | None = None
    emotional: Any | None = None
    mental: Any | None = None
    spiritual: Any | None = None
    narrative: Any | None = None
    statuses: Dict[str, str] = field(default_factory=dict)

    _tracer = _TRACER

    def initialize(self) -> Dict[str, str]:
        """Instantiate memory layers and emit a consolidated status event."""
        with self._tracer.start_as_current_span("memory.bundle.initialize") as span:
            statuses: Dict[str, str] = {}

            for layer in LAYERS:
                module_path = _LAYER_IMPORTS[layer]
                try:
                    module = import_module(module_path)
                    status = "ready"
                except ModuleNotFoundError:  # pragma: no cover - dependency missing
                    optional_path = f"memory.optional.{layer}"
                    try:
                        module = import_module(optional_path)
                        status = "skipped"
                    except ModuleNotFoundError:
                        module = None
                        status = "error"
                except Exception:  # pragma: no cover - unexpected import error
                    module = None
                    status = "error"

                if module is None:
                    statuses[layer] = status
                    continue

                setattr(self, layer, module)
                statuses[layer] = status

            span.set_attribute("memory.layers", ",".join(statuses.keys()))
            broadcast_layer_event(statuses)
            self.statuses = statuses
            return statuses

    def query(self, text: str) -> Dict[str, Any]:
        """Delegate to :func:`query_memory` to aggregate layer results."""
        with self._tracer.start_as_current_span("memory.bundle.query") as span:
            span.set_attribute("memory.query", text)
            return query_memory(text)


__all__ = ["MemoryBundle"]
