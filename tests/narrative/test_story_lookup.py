"""Verify joining of stories and events with filtering."""

from __future__ import annotations

from pathlib import Path

import pytest

from memory import narrative_engine, story_lookup

__version__ = "0.1.0"


@pytest.fixture
def setup_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Populate temporary narrative database with sample data."""

    db_path = tmp_path / "narrative.db"
    monkeypatch.setattr(narrative_engine, "DB_PATH", db_path)
    monkeypatch.setattr(narrative_engine, "CHROMA_DIR", tmp_path)
    records = [
        (1.0, "agent1", "alpha", "first story", {"n": 1}),
        (2.0, "agent2", "beta", "second tale", {"n": 2}),
    ]
    for ts, agent, etype, text, payload in records:
        narrative_engine.log_event(
            {"time": ts, "agent_id": agent, "event_type": etype, "payload": payload}
        )
        narrative_engine.index_story(agent, etype, text, ts)


def test_find_returns_joined_entries(setup_db: None) -> None:
    """All results include narrative text and event payload."""

    results = list(story_lookup.find())
    assert {r["text"] for r in results} == {"first story", "second tale"}
    payloads = {r["payload"]["n"] for r in results}
    assert payloads == {1, 2}


def test_find_filters(setup_db: None) -> None:
    """Filters narrow results by agent, event type, and text."""

    by_agent = list(story_lookup.find(agent_id="agent1"))
    assert len(by_agent) == 1 and by_agent[0]["text"] == "first story"
    by_type = list(story_lookup.find(event_type="beta"))
    assert len(by_type) == 1 and by_type[0]["agent_id"] == "agent2"
    by_text = list(story_lookup.find(text="tale"))
    assert len(by_text) == 1 and by_text[0]["event_type"] == "beta"
