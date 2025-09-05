"""Tests for the narrative story adapter."""

from __future__ import annotations

__version__ = "0.1.0"

import time

from agents.utils.story_adapter import get_recent_stories, watch_stories
from memory import narrative_engine


def _index(agent: str, text: str) -> None:
    ts = time.time()
    narrative_engine.index_story(agent, "event", text, timestamp=ts)
    narrative_engine.log_event(
        {
            "time": ts,
            "agent_id": agent,
            "event_type": "event",
            "payload": {},
        }
    )


def test_get_recent_stories(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "stories.db"
    monkeypatch.setattr(narrative_engine, "DB_PATH", db_path)

    _index("root_agent", "alpha")
    _index("root_agent", "beta")

    assert get_recent_stories("root_agent", limit=1) == ["beta"]


def test_watch_stories(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "stories.db"
    monkeypatch.setattr(narrative_engine, "DB_PATH", db_path)

    narrative_engine.log_story("one")
    narrative_engine.log_story("two")

    collected: list[str] = []
    watch_stories(collected.append)
    assert collected == ["one", "two"]
