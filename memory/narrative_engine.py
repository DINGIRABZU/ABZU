"""Stub narrative memory engine.

Provides interfaces for recording story events composed of an actor,
action and symbolism.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


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
