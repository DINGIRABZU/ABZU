import json
import sys
from pathlib import Path
import logging
import logging.config
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import emotion_registry


def test_state_persistence(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(emotion_registry, "STATE_FILE", state_file)
    emotion_registry._STATE.clear()
    emotion_registry._save_state()

    emotion_registry.set_current_layer("rubedo_layer")
    emotion_registry.set_last_emotion("joy")
    emotion_registry.set_resonance_level(0.75)
    emotion_registry.set_preferred_expression_channel("voice")

    data = json.loads(state_file.read_text())
    assert data["current_layer"] == "rubedo_layer"
    assert data["last_emotion"] == "joy"
    assert data["resonance_level"] == 0.75
    assert data["preferred_expression_channel"] == "voice"

    emotion_registry._STATE.clear()
    emotion_registry._load_state()
    assert emotion_registry.get_current_layer() == "rubedo_layer"
    assert emotion_registry.get_last_emotion() == "joy"
    assert emotion_registry.get_resonance_level() == 0.75
    assert emotion_registry.get_preferred_expression_channel() == "voice"


def test_emotion_logging(tmp_path, monkeypatch):
    config_path = ROOT / "logging_config.yaml"
    with config_path.open("r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    log_file = tmp_path / "INANNA_AI.log"
    config["handlers"]["file"]["filename"] = str(log_file)
    logging.config.dictConfig(config)

    state_file = tmp_path / "state.json"
    monkeypatch.setattr(emotion_registry, "STATE_FILE", state_file)
    emotion_registry._STATE.clear()
    emotion_registry._save_state()

    emotion_registry.set_last_emotion("anger")
    data = json.loads(log_file.read_text())
    assert data["emotion"] == "anger"
