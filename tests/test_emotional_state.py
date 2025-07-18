import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import emotional_state


def test_state_persistence(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(emotional_state, "STATE_FILE", state_file)
    emotional_state._STATE.clear()
    emotional_state._save_state()

    pairs = [(440.0, 880.0), (333.0, 666.0)]
    emotional_state.set_resonance_pairs(pairs)
    emotional_state.set_soul_state("awakened")

    data = json.loads(state_file.read_text())
    assert data["resonance_pairs"] == [[440.0, 880.0], [333.0, 666.0]]
    assert data["soul_state"] == "awakened"

    emotional_state._STATE.clear()
    emotional_state._load_state()
    assert emotional_state.get_resonance_pairs() == pairs
    assert emotional_state.get_soul_state() == "awakened"


def test_current_layer_round_trip(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(emotional_state, "STATE_FILE", state_file)
    emotional_state._STATE.clear()
    emotional_state._save_state()

    emotional_state.set_current_layer("citrinitas_layer")
    data = json.loads(state_file.read_text())
    assert data["current_layer"] == "citrinitas_layer"

    emotional_state._STATE.clear()
    emotional_state._load_state()
    assert emotional_state.get_current_layer() == "citrinitas_layer"
