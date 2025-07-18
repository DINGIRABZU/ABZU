import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import soul_state_manager
import emotional_state
import archetype_shift_engine as ase
import emotion_registry


def test_state_persistence(tmp_path, monkeypatch):
    tracker = tmp_path / "tracker.json"
    monkeypatch.setattr(soul_state_manager, "STATE_FILE", tracker)
    soul_state_manager._STATE.clear()
    soul_state_manager._save_state()

    soul_state_manager.update_archetype("albedo_layer")
    soul_state_manager.update_soul_state("awakened")

    data = json.loads(tracker.read_text())
    assert data["archetype"] == "albedo_layer"
    assert data["soul_state"] == "awakened"

    soul_state_manager._STATE.clear()
    soul_state_manager._load_state()
    state = soul_state_manager.get_state()
    assert state["archetype"] == "albedo_layer"
    assert state["soul_state"] == "awakened"


def test_emotional_state_integration(tmp_path, monkeypatch):
    tracker = tmp_path / "tracker.json"
    monkeypatch.setattr(soul_state_manager, "STATE_FILE", tracker)
    soul_state_manager._STATE.clear()
    soul_state_manager._save_state()

    state_file = tmp_path / "state.json"
    monkeypatch.setattr(emotional_state, "STATE_FILE", state_file)
    emotional_state._STATE.clear()
    emotional_state._save_state()

    emotional_state.set_soul_state("sleeping")

    data = json.loads(tracker.read_text())
    assert data["soul_state"] == "sleeping"


def test_archetype_shift_integration(tmp_path, monkeypatch):
    tracker = tmp_path / "tracker.json"
    monkeypatch.setattr(soul_state_manager, "STATE_FILE", tracker)
    soul_state_manager._STATE.clear()
    soul_state_manager._save_state()

    monkeypatch.setattr(emotion_registry, "get_resonance_level", lambda: 0.9)
    monkeypatch.setattr(emotion_registry, "get_current_layer", lambda: None)

    layer = ase.maybe_shift_archetype("hello", "anger")
    data = json.loads(tracker.read_text())

    assert layer == "nigredo_layer"
    assert data["archetype"] == "nigredo_layer"



