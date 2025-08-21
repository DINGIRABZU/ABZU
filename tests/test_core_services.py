from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.helpers import emotion_stub
from tests.helpers.config_stub import build_settings

config_mod = types.ModuleType("config")
config_mod.settings = build_settings()
config_mod.reload = lambda: None
sys.modules.setdefault("config", config_mod)

import INANNA_AI as ia_pkg

sys.modules["INANNA_AI.emotion_analysis"] = emotion_stub
sys.modules["emotional_state"] = types.SimpleNamespace(
    set_last_emotion=lambda e: None,
    set_resonance_level=lambda v: None,
    get_current_layer=lambda: None,
    set_current_layer=lambda layer: None,
    get_last_emotion=lambda: None,
)

from core.emotion_analyzer import EmotionAnalyzer
from core.memory_logger import MemoryLogger
from core.model_selector import ModelSelector


def test_emotion_analyzer_updates_mood():
    analyzer = EmotionAnalyzer()
    data = analyzer.analyze("joy")
    assert "emotion" in data
    assert analyzer.mood_state["joy"] > 0.0


def test_model_selector_choose(tmp_path: Path):
    db = tmp_path / "db.sqlite"
    selector = ModelSelector(db_path=db)
    choice = selector.choose("instructional", 0.2, [])
    assert choice == "deepseek"


def test_model_selector_select_model(monkeypatch):
    monkeypatch.setattr(
        "core.model_selector.vector_memory.query_vectors", lambda **kw: []
    )
    selector = ModelSelector()
    model = selector.select_model("instructional", "neutral", 0.2, [])
    assert model == "glm"


def test_memory_logger(monkeypatch):
    from core import memory_logger as ml_mod

    logged: dict[str, tuple] = {}

    def fake_log_interaction(text, meta, result, status):
        logged["interaction"] = (text, meta, result, status)

    def fake_load_interactions():
        return [{"input": "x"}]

    def fake_log_ritual(name, steps):
        logged["ritual"] = (name, steps)

    monkeypatch.setattr(ml_mod, "log_interaction", fake_log_interaction)
    monkeypatch.setattr(ml_mod, "load_interactions", fake_load_interactions)
    monkeypatch.setattr(ml_mod, "log_ritual_result", fake_log_ritual)

    logger = MemoryLogger()
    logger.log_interaction("hi", {"a": 1}, {"b": 2}, "ok")
    assert logged["interaction"][0] == "hi"
    assert logger.load_interactions() == [{"input": "x"}]
    logger.log_ritual_result("rit", ["step"])
    assert logged["ritual"] == ("rit", ["step"])
