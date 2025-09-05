"""Aggregated memory queries across cortex, vector, and spiral stores.

Each layer is queried independently so that failures in one layer do not
prevent returning results from the others. Any exceptions are logged and the
names of failing layers are collected in the ``failed_layers`` field.
"""

from __future__ import annotations

from typing import Any, Dict, List
import logging

from .cortex import query_spirals
from spiral_memory import spiral_recall
from vector_memory import query_vectors


logger = logging.getLogger(__name__)


def query_memory(query: str) -> Dict[str, Any]:
    """Return aggregated results across cortex, vector, and spiral memory."""

    failed_layers: List[str] = []

    try:
        cortex_res = query_spirals(text=query)
    except Exception:  # pragma: no cover - logged
        logger.exception("cortex query failed")
        cortex_res = []
        failed_layers.append("cortex")

    try:
        vector_res = query_vectors(filter={"text": query})
    except Exception:  # pragma: no cover - logged
        logger.exception("vector query failed")
        vector_res = []
        failed_layers.append("vector")

    try:
        spiral_res = spiral_recall(query)
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
