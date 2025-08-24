"""Tests for orchestrator."""

from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub optional dependencies before importing the module
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
yaml_mod = types.ModuleType("yaml")
yaml_mod.safe_load = lambda *a, **k: {}
sys.modules.setdefault("yaml", yaml_mod)
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sf_mod = sys.modules["soundfile"]
setattr(sf_mod, "write", lambda path, data, sr, subtype=None: Path(path).touch())

scipy_mod = types.ModuleType("scipy")
scipy_io = types.ModuleType("scipy.io")
wavfile_mod = types.ModuleType("scipy.io.wavfile")
wavfile_mod.write = lambda *a, **k: None
scipy_io.wavfile = wavfile_mod
signal_mod = types.ModuleType("scipy.signal")
signal_mod.butter = lambda *a, **k: (None, None)
signal_mod.lfilter = lambda *a, **k: []
scipy_mod.signal = signal_mod
scipy_mod.io = scipy_io
sys.modules.setdefault("scipy", scipy_mod)
sys.modules.setdefault("scipy.io", scipy_io)
sys.modules.setdefault("scipy.signal", signal_mod)
sys.modules.setdefault("scipy.io.wavfile", wavfile_mod)

from tests.helpers.config_stub import build_settings

config_mod = types.ModuleType("config")
config_mod.settings = build_settings()
config_mod.reload = lambda: None
sys.modules.setdefault("config", config_mod)

sp_pkg = types.ModuleType("SPIRAL_OS")
sp_pkg.qnl_engine = types.SimpleNamespace(
    parse_input=lambda text: {"tone": "neutral"},
    hex_to_song=lambda hex_input, duration_per_byte=0.05: (["phrase"], [0.0]),
)
sp_pkg.symbolic_parser = types.SimpleNamespace(
    parse_intent=lambda d: [],
    _gather_text=lambda d: "",
    _INTENTS={},
)
sys.modules.setdefault("SPIRAL_OS", sp_pkg)
sys.modules["SPIRAL_OS.qnl_engine"] = sp_pkg.qnl_engine
sys.modules["SPIRAL_OS.symbolic_parser"] = sp_pkg.symbolic_parser
sys.modules.setdefault(
    "training_guide", types.SimpleNamespace(log_result=lambda *a, **k: None)
)

import core.model_selector as ms_mod
import crown_decider
from rag import orchestrator
from rag.orchestrator import MoGEOrchestrator

# Disable invocation engine side effects for tests
orchestrator.invocation_engine.invoke = lambda *a, **k: []
orchestrator.invocation_engine._extract_symbols = lambda text: ""
orchestrator.vector_memory.add_vector = lambda *a, **k: None
orchestrator.vector_memory.query_vectors = lambda *a, **k: []
ms_mod.vector_memory = orchestrator.vector_memory


def test_route_text_only(tmp_path, monkeypatch):
    orch = MoGEOrchestrator()
    info = {"emotion": "joy"}
    monkeypatch.setattr(
        "INANNA_AI.corpus_memory.search_corpus",
        lambda *a, **k: [("p", "snippet")],
    )
    result = orch.route(
        "hello", info, text_modality=True, voice_modality=False, music_modality=False
    )
    assert result["plane"] == "ascension"
    assert "text" in result and result["text"]
    assert result["model"]


def test_route_voice(tmp_path, monkeypatch):
    monkeypatch.setattr(
        crown_decider,
        "decide_expression_options",
        lambda e: {
            "tts_backend": "gtts",
            "avatar_style": "a",
            "aura_amount": 0.5,
            "soul_state": "",
        },
    )
    orch = MoGEOrchestrator()
    info = {"emotion": "calm"}
    result = orch.route(
        "hi", info, text_modality=False, voice_modality=True, music_modality=False
    )
    assert result["plane"] == "ascension"
    assert Path(result["voice_path"]).exists()


def test_route_music(tmp_path):
    orch = MoGEOrchestrator()
    info = {"emotion": "joy"}
    result = orch.route(
        "hi", info, text_modality=False, voice_modality=False, music_modality=True
    )
    assert Path(result["music_path"]).exists()
    assert result["qnl_phrases"]


def test_route_qnl_voice(monkeypatch):
    orch = MoGEOrchestrator()
    info = {"emotion": "neutral"}
    qnl = {"tone": "rubedo"}

    def fake_modulate(text, tone):
        p = Path(f"{tone}.wav")
        p.touch()
        return str(p)

    monkeypatch.setattr(
        "INANNA_AI.voice_layer_albedo.modulate_voice",
        fake_modulate,
    )
    monkeypatch.setattr(
        "SPIRAL_OS.symbolic_parser.parse_intent",
        lambda d: ["ok"],
    )

    monkeypatch.setattr(
        crown_decider,
        "decide_expression_options",
        lambda e: {
            "tts_backend": "gtts",
            "avatar_style": "a",
            "aura_amount": 0.5,
            "soul_state": "",
        },
    )
    result = orch.route(
        "hi",
        info,
        qnl_data=qnl,
        text_modality=False,
        voice_modality=True,
        music_modality=False,
    )

    assert Path(result["voice_path"]).exists()
    assert result["qnl_intents"] == ["ok"]


def test_route_with_albedo_layer(monkeypatch):
    class DummyLayer:
        def __init__(self):
            self.calls = []

        def generate_response(self, text: str) -> str:
            self.calls.append(text)
            return f"albedo:{text}"

    layer = DummyLayer()
    orch = MoGEOrchestrator(albedo_layer=layer)
    info = {"emotion": "joy"}
    result = orch.route(
        "hello", info, text_modality=True, voice_modality=False, music_modality=False
    )
    assert result["text"] == "albedo:hello"
    assert layer.calls == ["hello"]


def test_context_model_selection(monkeypatch):
    orch = MoGEOrchestrator()
    monkeypatch.setattr(
        "INANNA_AI.corpus_memory.search_corpus",
        lambda *a, **k: [("p", "snippet")],
    )
    res1 = orch.route("I feel happy", {"emotion": "joy"})
    res2 = orch.route("import os", {"emotion": "neutral"})
    assert res2["model"] == res1["model"]


def test_handle_input_parses_and_routes(monkeypatch):
    events = {}

    def fake_parse(text):
        events["parse"] = text
        return {"tone": "joy"}

    def fake_intent(data):
        events["intent"] = data
        return ["ok"]

    def fake_route(self, text, emotion_data, *, qnl_data=None, **kwargs):
        events["route"] = qnl_data
        return {"result": True}

    monkeypatch.setattr(orchestrator.qnl_engine, "parse_input", fake_parse)
    monkeypatch.setattr(orchestrator.symbolic_parser, "parse_intent", fake_intent)
    monkeypatch.setattr(MoGEOrchestrator, "route", fake_route)
    monkeypatch.setattr(
        orchestrator.reflection_loop, "run_reflection_loop", lambda *a, **k: None
    )

    orch = MoGEOrchestrator()
    out = orch.handle_input("hello")

    assert events["parse"] == "hello"
    assert events["intent"] == {"tone": "joy"}
    assert events["route"] == {"tone": "joy"}
    assert out == {"result": True}


def test_handle_input_logs_analyze_audio_error(monkeypatch, caplog):
    """An exception in `listening_engine.analyze_audio` is logged."""

    # avoid heavy side effects
    monkeypatch.setattr(
        orchestrator.reflection_loop, "load_thresholds", lambda: {"default": 1.0}
    )
    monkeypatch.setattr(
        orchestrator.reflection_loop, "run_reflection_loop", lambda *a, **k: None
    )
    monkeypatch.setattr(MoGEOrchestrator, "route", lambda self, *a, **k: {})

    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(orchestrator.listening_engine, "analyze_audio", boom)

    orch = MoGEOrchestrator()
    with caplog.at_level("ERROR"):
        orch.handle_input("hello")

    assert any("analyze_audio failed" in r.getMessage() for r in caplog.records)


def test_schedule_action_executes(monkeypatch):
    called = []

    timer = orchestrator.schedule_action(lambda: called.append(True), 0.01)
    timer.join(0.1)

    assert called == [True]
