import sys
import types
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub heavy optional dependencies before importing orchestrator
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
np_mod = types.ModuleType("numpy")
np_mod.ndarray = list
np_mod.asarray = lambda x, dtype=None: x
sys.modules.setdefault("numpy", np_mod)
sys.modules.setdefault("requests", types.ModuleType("requests"))
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
sys.modules.setdefault("SPIRAL_OS", types.ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_engine", types.ModuleType("qnl_engine"))
sys.modules.setdefault("SPIRAL_OS.symbolic_parser", types.ModuleType("symbolic_parser"))
sys.modules.setdefault("SPIRAL_OS.qnl_utils", types.ModuleType("qnl_utils"))

import orchestrator
from orchestrator import MoGEOrchestrator
import corpus_memory_logging as cml


def test_silence_ritual_logged(monkeypatch, tmp_path, mock_emotion_state):
    log_path = tmp_path / "corpus_memory.json"
    monkeypatch.setattr(cml, "INTERACTIONS_FILE", log_path)

    monkeypatch.setattr(orchestrator.qnl_engine, "parse_input", lambda t: {"tone": "neutral"}, raising=False)
    monkeypatch.setattr(orchestrator.symbolic_parser, "parse_intent", lambda d: [], raising=False)
    monkeypatch.setattr(orchestrator.symbolic_parser, "_gather_text", lambda d: "", raising=False)
    monkeypatch.setattr(orchestrator.symbolic_parser, "_INTENTS", {}, raising=False)
    monkeypatch.setattr(MoGEOrchestrator, "route", lambda self, text, emotion_data, qnl_data=None: {})
    monkeypatch.setattr(orchestrator.reflection_loop, "run_reflection_loop", lambda *a, **k: None)
    monkeypatch.setattr(orchestrator.invocation_engine, "invoke", lambda *a, **k: [])
    monkeypatch.setattr(orchestrator.invocation_engine, "_extract_symbols", lambda t: "")
    monkeypatch.setattr(orchestrator, "ritual_action_sequence", lambda s, e: [])

    def fake_analyze(duration):
        return None, {"silence_meaning": "Extended silence – pause"}

    monkeypatch.setattr(orchestrator.listening_engine, "analyze_audio", fake_analyze)

    called = {}

    def fake_ritual(name):
        called["name"] = name
        return ["step"]

    monkeypatch.setattr(orchestrator.invocation_engine, "invoke_ritual", fake_ritual)

    orch = MoGEOrchestrator()
    orch.handle_input("hello")

    assert called["name"] == "silence_introspection"
    data = log_path.read_text(encoding="utf-8").splitlines()
    assert data, "log file should have an entry"
    record = json.loads(data[0])
    assert record["ritual"] == "silence_introspection"
    assert record["steps"] == ["step"]
