"""No-op narrative layer used when the real implementation is unavailable."""

from __future__ import annotations

__version__ = "0.2.0"

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Sequence


@dataclass
class StoryEvent:
    """Placeholder story event."""

    actor: str
    action: str
    symbolism: str | None = None


DB_PATH = Path("data/narrative_engine.db")
CHROMA_DIR = Path("data/narrative_events.chroma")


def log_story(text: str) -> None:  # pragma: no cover
    """Discard story text."""


def log_self_heal_story(
    text: str, component: str, patch: str
) -> None:  # pragma: no cover
    """Discard self-heal stories."""


def index_story(*args: Any, **kwargs: Any) -> None:  # pragma: no cover
    """Ignore story indexing."""


def stream_stories() -> Iterable[str]:
    """Yield no stored stories."""
    if False:
        yield ""


def compose_multitrack_story(
    events: Sequence[StoryEvent],
    *args: Any,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Return empty tracks for ``events``."""
    return {"prose": "", "audio": [], "visual": [], "usd": []}


def log_event(event: Dict[str, Any]) -> None:  # pragma: no cover
    """Discard narrative events."""


def query_events(*args: Any, **kwargs: Any) -> Iterator[Dict[str, Any]]:
    """Yield nothing as no events are stored."""
    if False:
        yield {}


def search_events(*args: Any, **kwargs: Any) -> Iterator[Dict[str, Any]]:
    """Yield nothing as no events are stored."""
    if False:
        yield {}


class NarrativeEngine:  # pragma: no cover - interface stub
    """Interface stub mirroring the real engine."""

    def record(self, event: StoryEvent) -> None:  # pragma: no cover - interface stub
        """Record a story event in the narrative store."""

    def stream(self) -> Iterable[StoryEvent]:  # pragma: no cover - interface stub
        """Iterate over stored story events."""
        return []


__all__ = [
    "StoryEvent",
    "NarrativeEngine",
    "log_story",
    "log_self_heal_story",
    "index_story",
    "stream_stories",
    "compose_multitrack_story",
    "log_event",
    "query_events",
    "search_events",
    "DB_PATH",
    "CHROMA_DIR",
]
