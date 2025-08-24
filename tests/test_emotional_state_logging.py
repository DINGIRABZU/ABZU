"""Smoke test for emotion event logging."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import emotional_state


def test_event_log_written(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_file = tmp_path / "state.json"
    registry_file = tmp_path / "registry.json"
    event_log = tmp_path / "events.jsonl"
    monkeypatch.setattr(emotional_state, "STATE_FILE", state_file)
    monkeypatch.setattr(emotional_state, "REGISTRY_FILE", registry_file)
    monkeypatch.setattr(emotional_state, "EVENT_LOG", event_log)
    emotional_state._STATE.clear()
    emotional_state._REGISTRY[:] = ["joy"]
    emotional_state._save_state()
    emotional_state._save_registry()

    emotional_state.set_last_emotion("joy")

    lines = event_log.read_text().strip().splitlines()
    assert lines, "event log should contain at least one entry"
    entry = json.loads(lines[-1])
    assert entry["event"] == "set_last_emotion"
    assert entry["emotion"] == "joy"
