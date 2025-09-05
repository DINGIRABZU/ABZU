"""No-op narrative layer used when the real implementation is unavailable."""

from __future__ import annotations

__version__ = "0.1.0"

from dataclasses import dataclass
from typing import Any, Dict, Iterator


@dataclass
class StoryEvent:
    """Placeholder story event."""

    actor: str
    action: str
    symbolism: str | None = None


def log_event(event: Dict[str, Any]) -> None:  # pragma: no cover - no side effects
    """Discard narrative events."""


def query_events(*args: Any, **kwargs: Any) -> Iterator[Dict[str, Any]]:
    """Yield nothing as no events are stored."""
    if False:
        yield {}


def search_events(*args: Any, **kwargs: Any) -> Iterator[Dict[str, Any]]:
    """Yield nothing as no events are stored."""
    if False:
        yield {}


__all__ = ["StoryEvent", "log_event", "query_events", "search_events"]
