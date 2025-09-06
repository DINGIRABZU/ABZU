"""No-op cortex layer used when the real implementation is unavailable."""

from __future__ import annotations

__version__ = "0.1.0"

from typing import Any, List


def query_spirals(*args: Any, **kwargs: Any) -> List[Any]:
    """Return an empty list as no cortex records are stored."""
    return []


__all__ = ["query_spirals"]
