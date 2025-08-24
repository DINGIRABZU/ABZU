"""Concurrency and persistence tests for emotional_state."""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import emotional_state


@pytest.fixture(autouse=True)
def _temp_state_files(tmp_path, monkeypatch):
    """Redirect persistence files to a temporary directory."""
    state_file = tmp_path / "state.json"
    registry_file = tmp_path / "registry.json"
    event_file = tmp_path / "events.log"
    monkeypatch.setattr(emotional_state, "STATE_FILE", state_file)
    monkeypatch.setattr(emotional_state, "REGISTRY_FILE", registry_file)
    monkeypatch.setattr(emotional_state, "EVENT_LOG", event_file)
    emotional_state._STATE.clear()
    emotional_state._REGISTRY.clear()
    emotional_state._save_state()
    emotional_state._save_registry()


def test_concurrent_updates():
    def worker(emotion: str) -> str | None:
        emotional_state.set_last_emotion(emotion)
        return emotional_state.get_last_emotion()

    with ThreadPoolExecutor() as ex:
        results = list(ex.map(worker, ("joy", "calm")))

    assert set(results) <= {"joy", "calm"}
    assert emotional_state.get_last_emotion() in {"joy", "calm"}
    registry = emotional_state.get_registered_emotions()
    assert "joy" in registry and "calm" in registry


def test_state_persistence_round_trip():
    emotional_state.set_last_emotion("joy")
    emotional_state.set_current_layer("albedo_layer")

    data = json.loads(emotional_state.STATE_FILE.read_text())
    assert data["last_emotion"] == "joy"
    assert data["current_layer"] == "albedo_layer"

    emotional_state._STATE.clear()
    emotional_state._REGISTRY.clear()
    emotional_state._load_state()
    emotional_state._load_registry()

    assert emotional_state.get_last_emotion() == "joy"
    assert emotional_state.get_current_layer() == "albedo_layer"
    assert "joy" in emotional_state.get_registered_emotions()
