"""Fallback search API returning no results."""

from __future__ import annotations

__version__ = "0.1.0"

from typing import Any, Dict, List


def aggregate_search(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
    """Return an empty list when search dependencies are unavailable."""
    return []


__all__ = ["aggregate_search"]
