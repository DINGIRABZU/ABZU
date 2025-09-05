"""Aggregated memory queries across cortex, vector, and spiral stores."""

from __future__ import annotations

from typing import Any, Dict
import logging

from .cortex import query_spirals
from spiral_memory import spiral_recall
from vector_memory import query_vectors


logger = logging.getLogger(__name__)


def query_memory(query: str) -> Dict[str, Any]:
    """Return aggregated results across cortex, vector, and spiral memory."""

    try:
        cortex_res = query_spirals(text=query)
    except Exception:  # pragma: no cover - logged
        logger.exception("cortex query failed")
        cortex_res = []

    try:
        vector_res = query_vectors(filter={"text": query})
    except Exception:  # pragma: no cover - logged
        logger.exception("vector query failed")
        vector_res = []

    try:
        spiral_res = spiral_recall(query)
    except Exception:  # pragma: no cover - logged
        logger.exception("spiral recall failed")
        spiral_res = ""

    return {"cortex": cortex_res, "vector": vector_res, "spiral": spiral_res}


__all__ = ["query_memory"]
