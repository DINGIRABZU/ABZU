"""Stub narrative memory engine.

Provides interfaces for recording story events composed of an actor,
action and symbolism.

Also includes simple helper functions for logging generated stories in
memory for later retrieval.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class StoryEvent:
    """A story beat linking an actor, an action and optional symbolism."""

    actor: str
    action: str
    symbolism: str | None = None


class NarrativeEngine:
    """Interface for working with narrative story events."""

    def record(self, event: StoryEvent) -> None:
        """Record a story event in the narrative store."""
        raise NotImplementedError

    def stream(self) -> Iterable[StoryEvent]:
        """Iterate over stored story events."""
        raise NotImplementedError


_STORY_LOG: List[str] = []


def log_story(text: str) -> None:
    """Append ``text`` to the in-memory story log."""

    _STORY_LOG.append(text)


def stream_stories() -> Iterable[str]:
    """Yield recorded stories in insertion order."""

    yield from list(_STORY_LOG)


__all__ = [
    "StoryEvent",
    "NarrativeEngine",
    "log_story",
    "stream_stories",
]
