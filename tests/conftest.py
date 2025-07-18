import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import emotional_state
import emotion_registry

@pytest.fixture()
def mock_emotion_state(tmp_path, monkeypatch):
    state_file = tmp_path / "emotion_state.json"
    monkeypatch.setattr(emotional_state, "STATE_FILE", state_file)
    monkeypatch.setattr(emotion_registry, "STATE_FILE", state_file)
    emotional_state._STATE.clear()
    emotion_registry._STATE.clear()
    emotional_state._save_state()
    emotion_registry._load_state()
    emotional_state.set_last_emotion("longing")
    emotional_state.set_resonance_level(0.75)
    return state_file
