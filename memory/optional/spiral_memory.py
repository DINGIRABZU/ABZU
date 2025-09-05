"""No-op spiral memory used when the real implementation is unavailable."""

from __future__ import annotations

__version__ = "0.1.0"


from typing import Any


def spiral_recall(*args: Any, **kwargs: Any) -> str:
    """Return an empty string as no spiral data are stored."""
    return ""


__all__ = ["spiral_recall"]
