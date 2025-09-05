"""No-op spiritual layer used when the real implementation is unavailable."""

from __future__ import annotations

__version__ = "0.1.0"

from typing import Any, List, Optional


def set_event_symbol(event: str, symbol: str, *args: Any, **kwargs: Any) -> None:
    """Discard event-symbol mappings."""


def map_to_symbol(event_metadata: Any, *args: Any, **kwargs: Any) -> None:
    """Discard mappings passed via specification-aligned interface."""


def get_event_symbol(event: str, *args: Any, **kwargs: Any) -> Optional[str]:
    """Return ``None`` as no mappings are stored."""
    return None


def lookup_symbol_history(symbol: str, *args: Any, **kwargs: Any) -> List[str]:
    """Return an empty list as no mappings are stored."""
    return []


def get_connection(*args: Any, **kwargs: Any) -> None:
    """Return ``None`` to indicate no database connection."""
    return None


__all__ = [
    "set_event_symbol",
    "map_to_symbol",
    "get_event_symbol",
    "lookup_symbol_history",
    "get_connection",
]
