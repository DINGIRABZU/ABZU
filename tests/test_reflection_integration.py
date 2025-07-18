import sys
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub heavy optional dependencies before importing orchestrator
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
sys.modules.setdefault("numpy", types.ModuleType("numpy"))
sys.modules["numpy"].ndarray = object
sys.modules["numpy"].float32 = float
sys.modules["numpy"].int16 = "int16"
sys.modules["numpy"].random = types.SimpleNamespace(rand=lambda *a, **k: 0)
_yaml = types.ModuleType("yaml")
_yaml.safe_load = lambda *a, **k: {}
sys.modules.setdefault("yaml", _yaml)
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

import orchestrator
from orchestrator import MoGEOrchestrator, context_tracker

# Disable invocation engine side effects
orchestrator.invocation_engine.invoke = lambda *a, **k: []
orchestrator.invocation_engine._extract_symbols = lambda text: ""


def test_reflection_runs_when_avatar_loaded(monkeypatch):
    called = {"reflect": 0}

    monkeypatch.setattr(orchestrator.qnl_engine, "parse_input", lambda t: {"tone": "neutral"})
    monkeypatch.setattr(orchestrator.symbolic_parser, "parse_intent", lambda d: [])
    monkeypatch.setattr(MoGEOrchestrator, "route", lambda self, text, emotion_data, *, qnl_data=None, **kw: {})

    def fake_reflect(*args, **kwargs):
        called["reflect"] += 1
    monkeypatch.setattr(orchestrator.reflection_loop, "run_reflection_loop", fake_reflect)

    context_tracker.state.avatar_loaded = True

    orch = MoGEOrchestrator()
    orch.handle_input("hello")

    assert called["reflect"] == 1
