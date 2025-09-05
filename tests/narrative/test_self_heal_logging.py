"""Tests for self-heal narrative logging."""

from __future__ import annotations

import json

from citadel.event_producer import Event
from agents.nazarick import narrative_scribe as ns
from memory import narrative_engine, cortex


__version__ = "0.1.0"


def test_self_heal_event_logged(tmp_path, monkeypatch):
    log_file = tmp_path / "story.log"
    db_path = tmp_path / "stories.db"
    patch_file = tmp_path / "patches.jsonl"

    monkeypatch.setattr(ns, "LOG_FILE", log_file)
    monkeypatch.setattr(narrative_engine, "DB_PATH", db_path)
    monkeypatch.setattr(cortex, "PATCH_LINKS_FILE", patch_file)

    def fake_personas():
        return {
            "default": {
                "tone": "hopeful",
                "self_heal_template": "{agent} restored {component} with patch {patch}",
            }
        }

    monkeypatch.setattr(ns, "_load_personas", fake_personas)

    scribe = ns.NarrativeScribe()
    event = Event(
        agent_id="a",
        event_type="self_heal",
        payload={"component": "core", "patch": "abc"},
    )
    scribe.process_event(event)

    text = log_file.read_text().strip()
    assert text == "a restored core with patch abc"
    stories = list(narrative_engine.stream_stories())
    assert stories[-1] == text

    entry = json.loads(patch_file.read_text().splitlines()[-1])
    assert entry["component"] == "core"
    assert entry["patch"] == "abc"
    assert entry["story"] == text
