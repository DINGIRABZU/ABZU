"""Aggregate memory queries across cortex, vector store and spiral layers.

``query_memory`` queries each layer independently and merges the results into
one dictionary. Errors in individual layers are captured so that partial
results can still be returned alongside a list of failing layers.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

__version__ = "0.1.0"


try:  # pragma: no cover - cortex layer may be unavailable
    from .cortex import query_spirals

    def query_cortex(prompt: str) -> List[Dict[str, Any]]:
        return query_spirals(text=prompt)

except Exception:  # pragma: no cover - dependency may be missing
    try:  # optional fallback
        from .optional.cortex import query_spirals  # type: ignore

        def query_cortex(
            prompt: str,
        ) -> List[Dict[str, Any]]:  # pragma: no cover - passthrough
            return query_spirals(text=prompt)

    except Exception:  # pragma: no cover - final fallback

        def query_spirals(*_: Any, **__: Any) -> List[Dict[str, Any]]:
            return []

        def query_cortex(
            prompt: str,
        ) -> List[Dict[str, Any]]:  # pragma: no cover - fallback
            return []


try:  # pragma: no cover - vector store may be unavailable
    from vector_memory import query_vectors

    def query_vector_store(prompt: str) -> List[Dict[str, Any]]:
        return query_vectors(filter={"text": prompt})

except Exception:  # pragma: no cover - dependency may be missing
    try:  # optional fallback
        from .optional import vector_memory as _vector_memory

        def query_vector_store(
            prompt: str,
        ) -> List[Dict[str, Any]]:  # pragma: no cover - passthrough
            return _vector_memory.query_vectors(filter={"text": prompt})

        query_vectors = _vector_memory.query_vectors

    except Exception:  # pragma: no cover - final fallback

        def query_vectors(*_: Any, **__: Any) -> List[Dict[str, Any]]:
            return []

        def query_vector_store(
            prompt: str,
        ) -> List[Dict[str, Any]]:  # pragma: no cover - fallback
            return []


try:  # pragma: no cover - spiral memory may be unavailable
    from spiral_memory import spiral_recall
except Exception:  # pragma: no cover - dependency may be missing
    try:
        from .optional import spiral_memory as _spiral_memory

        def spiral_recall(query: str) -> str:  # pragma: no cover - passthrough
            return _spiral_memory.spiral_recall(query)

    except Exception:  # pragma: no cover - final fallback

        def spiral_recall(query: str) -> str:  # pragma: no cover - fallback
            return ""


logger = logging.getLogger(__name__)


def query_memory(prompt: str) -> Dict[str, Any]:
    """Return aggregated results from cortex, vector and spiral memory layers."""

    failed_layers: List[str] = []

    try:
        cortex_res = query_cortex(prompt)
    except Exception:  # pragma: no cover - logged
        logger.exception("cortex query failed")
        cortex_res = []
        failed_layers.append("cortex")

    try:
        vector_res = query_vector_store(prompt)
    except Exception:  # pragma: no cover - logged
        logger.exception("vector query failed")
        vector_res = []
        failed_layers.append("vector")

    try:
        spiral_res = spiral_recall(prompt)
    except Exception:  # pragma: no cover - logged
        logger.exception("spiral recall failed")
        spiral_res = ""
        failed_layers.append("spiral")

    return {
        "cortex": cortex_res,
        "vector": vector_res,
        "spiral": spiral_res,
        "failed_layers": failed_layers,
    }


__all__ = ["query_memory"]
