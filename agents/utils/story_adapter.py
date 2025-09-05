"""Adapters for retrieving narrative stories for agents."""

from __future__ import annotations

__version__ = "0.1.0"

from typing import Callable

from memory import narrative_engine, story_lookup


def get_recent_stories(agent_id: str, limit: int = 50) -> list[str]:
    """Return the most recent story texts for ``agent_id``.

    Parameters
    ----------
    agent_id:
        Agent identifier to filter stories.
    limit:
        Maximum number of stories to return.
    """
    records = list(story_lookup.find(agent_id=agent_id))
    return [r["text"] for r in records][-limit:]


def watch_stories(callback: Callable[[str], None]) -> None:
    """Stream recorded stories and invoke ``callback`` for each."""
    for story in narrative_engine.stream_stories():
        callback(story)


__all__ = ["get_recent_stories", "watch_stories"]
