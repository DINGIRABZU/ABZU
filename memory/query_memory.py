"""Aggregated memory queries across cortex, vector, and spiral stores.

Each layer is queried independently so that failures in one layer do not
prevent returning results from the others. Any exceptions are logged and the
names of failing layers are collected in the ``failed_layers`` field.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from opentelemetry import trace

try:  # pragma: no cover - cortex may be unavailable
    from .cortex import query_spirals
except Exception:  # pragma: no cover - logged lazily
    try:
        from .optional.cortex import query_spirals
    except Exception:

        def query_spirals(*args: Any, **kwargs: Any) -> list[Any]:
            """Fallback returning no cortex results."""
            return []


try:  # pragma: no cover - optional dependency
    from vector_memory import query_vectors as _query_vectors
except Exception:  # pragma: no cover - dependency may be missing
    try:
        from .optional import vector_memory as _vector_memory

        def _query_vectors(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
            return _vector_memory.query_vectors(*args, **kwargs)

    except Exception:  # pragma: no cover - fallback missing

        def _query_vectors(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
            return []


query_vectors = _query_vectors

_tracer = trace.get_tracer(__name__)

try:  # pragma: no cover - optional dependency
    from spiral_memory import spiral_recall as _spiral_recall
except Exception:  # pragma: no cover - dependency may be missing
    try:
        from .optional import spiral_memory as _spiral_memory

        def _spiral_recall(*args: Any, **kwargs: Any) -> str:
            return _spiral_memory.spiral_recall(*args, **kwargs)

    except Exception:  # pragma: no cover - fallback missing

        def _spiral_recall(*args: Any, **kwargs: Any) -> str:
            return ""


spiral_recall = _spiral_recall


logger = logging.getLogger(__name__)


def query_memory(query: str) -> Dict[str, Any]:
    """Return aggregated results across cortex, vector, and spiral memory."""

    with _tracer.start_as_current_span("memory.query") as span:
        span.set_attribute("memory.query", query)
        failed_layers: List[str] = []

        try:
            with _tracer.start_as_current_span("memory.cortex"):
                cortex_res = query_spirals(text=query)
        except Exception:  # pragma: no cover - logged
            logger.exception("cortex query failed")
            cortex_res = []
            failed_layers.append("cortex")

        try:
            with _tracer.start_as_current_span("memory.vector"):
                vector_res = query_vectors(filter={"text": query})
        except Exception:  # pragma: no cover - logged
            logger.exception("vector query failed")
            vector_res = []
            failed_layers.append("vector")

        try:
            with _tracer.start_as_current_span("memory.spiral"):
                spiral_res = spiral_recall(query)
        except Exception:  # pragma: no cover - logged
            logger.exception("spiral recall failed")
            spiral_res = ""
            failed_layers.append("spiral")

        if failed_layers:
            span.set_attribute("memory.failed_layers", ",".join(failed_layers))
            logger.warning("query_memory partial failure: %s", ", ".join(failed_layers))

        return {
            "cortex": cortex_res,
            "vector": vector_res,
            "spiral": spiral_res,
            "failed_layers": failed_layers,
        }


__all__ = ["query_memory"]
