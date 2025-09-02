"""Tests for narrative scribe."""

from __future__ import annotations

from citadel.event_producer import Event
from memory import narrative_engine

from agents.nazarick import narrative_scribe as ns

__version__ = "0.1.0"


def test_process_event_writes_log_and_memory(tmp_path, monkeypatch):
    monkeypatch.setattr(ns, "LOG_FILE", tmp_path / "story.log")
    monkeypatch.setattr(narrative_engine, "DB_PATH", tmp_path / "stories.db")

    def fake_personas():
        return {
            "default": {
                "tone": "neutral",
                "template": "{agent} {event_type} {payload}",
            }
        }

    monkeypatch.setattr(ns, "_load_personas", fake_personas)

    scribe = ns.NarrativeScribe()
    event = Event(agent_id="a", event_type="did", payload={"x": 1})
    scribe.process_event(event)

    text = (tmp_path / "story.log").read_text().strip()
    assert text == 'a did {"x": 1}'
    stories = list(narrative_engine.stream_stories())
    assert stories[-1] == text
