"""No-op vector memory used when the real implementation is unavailable."""

from __future__ import annotations

__version__ = "0.1.0"

from typing import Any, Dict, List


def query_vectors(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
    """Return an empty list as no vectors are stored."""
    return []


def search(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
    """Return an empty list for search requests."""
    return []


def add_vector(*args: Any, **kwargs: Any) -> None:
    """Discard vectors instead of persisting them."""


__all__ = ["query_vectors", "search", "add_vector"]
