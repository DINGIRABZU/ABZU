import sys
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub heavy optional dependencies before importing orchestrator
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
sf_mod = sys.modules["soundfile"]
setattr(sf_mod, "write", lambda path, data, sr, subtype=None: Path(path).touch())
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


def test_voice_modality_records_memory(monkeypatch, tmp_path):
    orch = MoGEOrchestrator()
    info = {"emotion": "joy"}

    monkeypatch.setattr(
        "INANNA_AI.corpus_memory.search_corpus",
        lambda *a, **k: [("p", "snippet")],
    )

    added = []

    def fake_add(text: str, meta: dict) -> None:
        added.append(meta)

    monkeypatch.setattr(orchestrator.vector_memory, "add_vector", fake_add)
    monkeypatch.setattr(orchestrator.vector_memory, "query_vectors", lambda *a, **k: [])

    logged = {}

    def fake_log(input_text: str, intent: dict, result: dict, outcome: str) -> None:
        logged.update({
            "input": input_text,
            "intent": intent,
            "result": result,
            "outcome": outcome,
        })

    monkeypatch.setattr(orchestrator, "log_interaction", fake_log)
    voice_path = tmp_path / "voice.wav"
    monkeypatch.setattr(orchestrator.language_engine, "synthesize_speech", lambda t, e: str(voice_path))
    monkeypatch.setattr(orchestrator.voice_aura, "apply_voice_aura", lambda p, **k: p)
    monkeypatch.setattr(
        orchestrator.crown_decider,
        "decide_expression_options",
        lambda e: {
            "tts_backend": "coqui",
            "avatar_style": "Soprano",
            "aura_amount": 0.3,
            "soul_state": "awakened",
        },
    )

    result = orch.route("hello", info, text_modality=True, voice_modality=True)

    types_ = {m.get("type") for m in added}
    assert "routing_decision" in types_
    assert "expression_decision" in types_
    assert result["voice_path"] == str(voice_path)
    assert logged["input"] == "hello"
    assert logged["result"]["tts_backend"] == "coqui"


def test_show_avatar_logging(monkeypatch):
    orch = MoGEOrchestrator()

    monkeypatch.setattr(orchestrator.qnl_engine, "parse_input", lambda t: {"tone": "neutral"})
    monkeypatch.setattr(orchestrator.symbolic_parser, "parse_intent", lambda d: [])
    monkeypatch.setattr(orchestrator.symbolic_parser, "_gather_text", lambda d: "")
    monkeypatch.setattr(orchestrator.symbolic_parser, "_INTENTS", {})
    monkeypatch.setattr(orchestrator.reflection_loop, "run_reflection_loop", lambda *a, **k: None)
    monkeypatch.setattr(orchestrator.listening_engine, "analyze_audio", lambda d: (None, {}))

    logged = {}

    def fake_log(text: str, intent: dict, result: dict, outcome: str) -> None:
        logged.update({"intent": intent, "result": result, "outcome": outcome})

    monkeypatch.setattr(orchestrator, "log_interaction", fake_log)

    orch.handle_input("appear to me")

    assert logged["intent"] == {"action": "show_avatar"}
    assert "message" in logged["result"]
    assert logged["outcome"] == "ok"
