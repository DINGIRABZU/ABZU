import sys
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub heavy optional dependencies before importing orchestrator
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
fs_mod = sys.modules["soundfile"]
setattr(fs_mod, "write", lambda path, data, sr, subtype=None: Path(path).touch())
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
yaml_mod = types.ModuleType("yaml")
yaml_mod.safe_load = lambda *a, **k: {}
sys.modules.setdefault("yaml", yaml_mod)
dummy_np = types.ModuleType("numpy")
dummy_np.asarray = lambda x, dtype=None: x
dummy_np.linalg = types.SimpleNamespace(norm=lambda x: 1.0)
dummy_np.ndarray = object
dummy_np.float32 = float
dummy_np.int16 = "int16"
dummy_np.random = types.SimpleNamespace(rand=lambda *a, **k: 0)
dummy_np.pi = 3.141592653589793
dummy_np.array = lambda x, dtype=None: list(x)
sys.modules.setdefault("numpy", dummy_np)
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
qnl_stub.parse_input = lambda t: {"tone": "neutral"}
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


def test_avatar_state_logging(monkeypatch):
    orch = MoGEOrchestrator()

    monkeypatch.setattr(orchestrator.reflection_loop, "run_reflection_loop", lambda *a, **k: None)
    monkeypatch.setattr(orchestrator.listening_engine, "analyze_audio", lambda d: (None, {}))
    monkeypatch.setattr(orchestrator.vector_memory, "add_vector", lambda *a, **k: None)
    monkeypatch.setattr(orchestrator.vector_memory, "query_vectors", lambda *a, **k: [])
    monkeypatch.setattr("INANNA_AI.corpus_memory.search_corpus", lambda *a, **k: [("p", "snippet")])
    monkeypatch.setattr(
        orchestrator.crown_decider,
        "decide_expression_options",
        lambda e: {
            "tts_backend": "coqui",
            "avatar_style": "Soprano",
            "aura_amount": 0.4,
            "soul_state": "awakened",
        },
    )

    logged = {}

    def fake_log(text: str, intent: dict, result: dict, outcome: str) -> None:
        if not logged:
            logged.update({"intent": intent, "result": result, "outcome": outcome})

    monkeypatch.setattr(orchestrator, "log_interaction", fake_log)

    orch.handle_input("appear to me")

    assert logged["intent"] == {"action": "show_avatar"}
    assert logged["result"]["avatar_style"] == "Soprano"
    assert logged["result"]["aura_amount"] == 0.4
    assert logged["outcome"] == "ok"
