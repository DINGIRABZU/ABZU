import types
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI import main as voice_main
import pytest


class DummyLayerA:
    pass

class DummyLayerB:
    pass


def setup_basic(monkeypatch):
    monkeypatch.setattr(voice_main.utils, "setup_logger", lambda: None)
    monkeypatch.setattr(voice_main.db_storage, "init_db", lambda: None)
    monkeypatch.setattr(voice_main.db_storage, "save_interaction", lambda *a, **k: None)

    class DummyEngine:
        def record(self, duration):
            return "a.wav", {"emotion": "calm"}

    monkeypatch.setattr(voice_main.listening_engine, "ListeningEngine", lambda: DummyEngine())
    monkeypatch.setattr(voice_main.stt_whisper, "transcribe_audio", lambda p: "hi")

    class DummyGate:
        def process_inward(self, text):
            return ["vec"]

        def process_outward(self, grid):
            return "gate"

    monkeypatch.setattr(voice_main, "GateOrchestrator", lambda: DummyGate())
    monkeypatch.setattr(
        voice_main,
        "RFA7D",
        lambda: type("C", (), {"execute": lambda self, v: [1], "grid": type("G", (), {"size": 1})()})(),
    )
    monkeypatch.setattr(
        voice_main.speaking_engine,
        "SpeakingEngine",
        lambda: type("S", (), {"speak": lambda self, t, e: "v.wav"})(),
    )


def test_registry_multiple_layers(monkeypatch):
    setup_basic(monkeypatch)
    created = {}

    def make_a():
        created["a"] = True
        return DummyLayerA()

    def make_b():
        created["b"] = True
        return DummyLayerB()

    monkeypatch.setattr(voice_main, "REGISTRY", {"a": make_a, "b": make_b})
    monkeypatch.setattr(voice_main, "list_personalities", lambda: ["a", "b"])

    class DummyOrch:
        def __init__(self, *, albedo_layer=None):
            created["layer"] = albedo_layer

        def route(self, *a, **k):
            return {"text": "reply"}

    monkeypatch.setattr(voice_main, "MoGEOrchestrator", DummyOrch)

    voice_main.main(["--duration", "0", "--personality", "b"])

    assert created.get("b")
    assert isinstance(created.get("layer"), DummyLayerB)


def test_help_lists_layers(monkeypatch, capsys):
    monkeypatch.setattr(voice_main, "REGISTRY", {"b": DummyLayerB, "a": DummyLayerA})
    monkeypatch.setattr(voice_main, "list_personalities", lambda: ["a", "b"])
    with pytest.raises(SystemExit):
        voice_main.main(["--help"])
    out = capsys.readouterr().out
    assert "a" in out and "b" in out


def test_list_personalities_sorted():
    from INANNA_AI.personality_layers import list_personalities, REGISTRY

    original = REGISTRY.copy()
    try:
        REGISTRY.clear()
        REGISTRY.update({"b": DummyLayerB, "a": DummyLayerA})
        assert list_personalities() == ["a", "b"]
    finally:
        REGISTRY.clear()
        REGISTRY.update(original)
