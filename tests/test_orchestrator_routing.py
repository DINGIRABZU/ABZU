import sys
from pathlib import Path
import numpy as np
import os

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import types
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
sf_mod = sys.modules["soundfile"]; setattr(sf_mod, "write", lambda path, data, sr, subtype=None: Path(path).touch())
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
yaml_mod = types.ModuleType("yaml")
yaml_mod.safe_load = lambda *a, **k: {}
sys.modules.setdefault("yaml", yaml_mod)
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
sp_mod = sys.modules.setdefault("SPIRAL_OS", types.ModuleType("SPIRAL_OS"))
qnl_stub = types.ModuleType("qnl_engine")
qnl_stub.hex_to_song = lambda x, duration_per_byte=1.0: ([], None)
qnl_stub.parse_input = lambda t: {}
sys.modules.setdefault("SPIRAL_OS.qnl_engine", qnl_stub)
setattr(sp_mod, "qnl_engine", qnl_stub)
sym_stub = types.ModuleType("symbolic_parser")
sym_stub._gather_text = lambda d: ""
sym_stub._INTENTS = {}
sym_stub.parse_intent = lambda d: []
sys.modules.setdefault("SPIRAL_OS.symbolic_parser", sym_stub)
setattr(sp_mod, "symbolic_parser", sym_stub)
stable_mod = types.ModuleType("stable_baselines3")
stable_mod.PPO = lambda *a, **k: object()
gym_mod = types.ModuleType("gymnasium")
gym_mod.Env = object
gym_mod.spaces = types.SimpleNamespace(Box=lambda **k: None)
sys.modules.setdefault("stable_baselines3", stable_mod)
sys.modules.setdefault("gymnasium", gym_mod)

from orchestrator import MoGEOrchestrator
import orchestrator


def test_route_all_modalities(monkeypatch, tmp_path):
    orch = MoGEOrchestrator()
    info = {"emotion": "joy"}

    monkeypatch.setattr(
        "INANNA_AI.corpus_memory.search_corpus",
        lambda *a, **k: [("p", "snippet")],
    )

    monkeypatch.setattr("orchestrator.vector_memory.add_vector", lambda *a, **k: None)
    monkeypatch.setattr("orchestrator.vector_memory.query_vectors", lambda *a, **k: [])

    voice_path = tmp_path / "voice.wav"
    monkeypatch.setattr(
        "INANNA_AI.tts_coqui.synthesize_speech",
        lambda text, emotion: str(voice_path),
    )
    monkeypatch.setattr("orchestrator.voice_aura.apply_voice_aura", lambda p, **k: p)

    dummy_wave = np.zeros(10, dtype=np.int16)
    monkeypatch.setattr(
        "SPIRAL_OS.qnl_engine.hex_to_song",
        lambda x, duration_per_byte=1.0: ([{"phrase": "p"}], dummy_wave),
    )

    written = {}

    def fake_write(path, wave, sr):
        written["path"] = path
        written["wave"] = wave
        written["sr"] = sr
    monkeypatch.setattr("orchestrator.sf.write", fake_write)

    result = orch.route(
        "hello",
        info,
        text_modality=True,
        voice_modality=True,
        music_modality=True,
    )

    assert result["plane"] in {"ascension", "underworld"}
    assert result["text"]
    assert result["voice_path"] == str(voice_path)
    assert result["music_path"] == str(written["path"])
    assert result["qnl_phrases"] == [{"phrase": "p"}]
    assert isinstance(written["wave"], np.ndarray)
    assert written["sr"] == 44100


def test_emotion_matrix_routing(monkeypatch):
    orch = MoGEOrchestrator()
    info = {"emotion": "stress"}

    monkeypatch.setattr("INANNA_AI.corpus_memory.search_corpus", lambda *a, **k: [("p", "s")])
    logs = {}
    monkeypatch.setattr("orchestrator.vector_memory.add_vector", lambda t, m: logs.setdefault("model", m["selected_model"]))
    monkeypatch.setattr("orchestrator.vector_memory.query_vectors", lambda *a, **k: [])

    result = orch.route("hello", info)

    assert result["model"] == "mistral"
    assert logs["model"] == "mistral"


def test_fallback_to_glm(monkeypatch):
    class BadLayer:
        def generate_response(self, text: str) -> str:
            raise RuntimeError("fail")

    orch = MoGEOrchestrator(albedo_layer=BadLayer())
    info = {"emotion": "joy"}

    monkeypatch.setattr("INANNA_AI.corpus_memory.search_corpus", lambda *a, **k: [("p", "s")])
    monkeypatch.setattr("orchestrator.vector_memory.add_vector", lambda *a, **k: None)
    monkeypatch.setattr("orchestrator.vector_memory.query_vectors", lambda *a, **k: [])

    result = orch.route("hello", info, text_modality=True)

    assert result["model"] == "glm"


def test_expression_decision(monkeypatch, tmp_path):
    orch = MoGEOrchestrator()
    info = {"emotion": "joy"}

    monkeypatch.setattr("INANNA_AI.corpus_memory.search_corpus", lambda *a, **k: [("p", "s")])
    voice_path = tmp_path / "voice.wav"
    monkeypatch.setattr("INANNA_AI.tts_coqui.synthesize_speech", lambda *a, **k: str(voice_path))
    monkeypatch.setattr("orchestrator.voice_aura.apply_voice_aura", lambda p, **k: p)
    monkeypatch.setenv("CROWN_TTS_BACKEND", "gtts")

    monkeypatch.setattr(
        "orchestrator.crown_decider.decide_expression_options",
        lambda e: {"tts_backend": "coqui", "avatar_style": "Soprano", "aura_amount": 0.3, "soul_state": "awakened"},
    )

    logged = {}
    monkeypatch.setattr("orchestrator.vector_memory.add_vector", lambda t, m: logged.update(m))
    monkeypatch.setattr("orchestrator.vector_memory.query_vectors", lambda *a, **k: [])

    result = orch.route("hello", info, text_modality=True, voice_modality=True)

    assert result["tts_backend"] == "coqui"
    assert result["avatar_style"] == "Soprano"
    assert result["aura_amount"] == 0.3
    assert logged["tts_backend"] == "coqui"
    assert os.getenv("CROWN_TTS_BACKEND") == "coqui"


def test_memory_biases_model_choice(monkeypatch):
    orch = MoGEOrchestrator()
    info = {"emotion": "joy"}

    history = [
        {"selected_model": "mistral", "emotion": "joy"},
        {"selected_model": "mistral", "emotion": "joy"},
    ]

    monkeypatch.setattr("orchestrator.vector_memory.query_vectors", lambda *a, **k: history)
    monkeypatch.setattr("orchestrator.vector_memory.add_vector", lambda *a, **k: None)
    monkeypatch.setattr("INANNA_AI.corpus_memory.search_corpus", lambda *a, **k: [("p", "s")])

    result = orch.route("hello", info)

    assert result["model"] == "mistral"


def test_choose_model_and_mood_update(monkeypatch):
    monkeypatch.setattr(orchestrator.qnl_engine, "parse_input", lambda t: {"tone": "stress"})
    monkeypatch.setattr(orchestrator.symbolic_parser, "parse_intent", lambda d: [])
    monkeypatch.setattr(orchestrator.symbolic_parser, "_gather_text", lambda d: "")
    monkeypatch.setattr(orchestrator.symbolic_parser, "_INTENTS", {})
    monkeypatch.setattr(MoGEOrchestrator, "route", lambda self, text, emotion_data, qnl_data=None, **k: {})
    monkeypatch.setattr(orchestrator.reflection_loop, "run_reflection_loop", lambda *a, **k: None)
    monkeypatch.setattr(orchestrator.invocation_engine, "invoke", lambda *a, **k: [])
    monkeypatch.setattr(orchestrator.invocation_engine, "_extract_symbols", lambda t: "")

    orch = MoGEOrchestrator()
    stress_before = orch.mood_state.get("stress", 0.0)
    neutral_before = orch.mood_state.get("neutral", 0.0)

    orch.handle_input("hello")

    assert orch.mood_state["stress"] > stress_before
    assert orch.mood_state["neutral"] < neutral_before

    weights = {"glm": 1.0, "deepseek": 1.0, "mistral": 2.0}
    choice = orch._choose_model("instructional", 0.9, ["emotional"], weights=weights)
    assert choice == "mistral"
