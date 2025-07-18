import sys
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
import json
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub heavy dependencies as in test_start_spiral_os
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("numpy", types.ModuleType("numpy"))
sys.modules["numpy"].random = types.SimpleNamespace(rand=lambda *a, **k: 0)
sys.modules["numpy"].int16 = "int16"
sys.modules["numpy"].float32 = float
sys.modules["numpy"].ndarray = object
scipy_mod = types.ModuleType("scipy")
scipy_io = types.ModuleType("scipy.io")
wavfile_mod = types.ModuleType("scipy.io.wavfile")
wavfile_mod.write = lambda *a, **k: None
scipy_io.wavfile = wavfile_mod
scipy_mod.io = scipy_io
signal_mod = types.ModuleType("scipy.signal")
signal_mod.butter = lambda *a, **k: (None, None)
signal_mod.lfilter = lambda *a, **k: []
scipy_mod.signal = signal_mod
sys.modules.setdefault("scipy.signal", signal_mod)
mod_sf = types.ModuleType("soundfile")
mod_sf.write = lambda *a, **k: None
sys.modules.setdefault("scipy", scipy_mod)
sys.modules.setdefault("scipy.io", scipy_io)
sys.modules.setdefault("scipy.io.wavfile", wavfile_mod)
stable_mod = types.ModuleType("stable_baselines3")
stable_mod.PPO = lambda *a, **k: object()
gym_mod = types.ModuleType("gymnasium")
gym_mod.Env = object
gym_mod.spaces = types.SimpleNamespace(Box=lambda **k: None)
sys.modules.setdefault("stable_baselines3", stable_mod)
sys.modules.setdefault("gymnasium", gym_mod)
sys.modules.setdefault("soundfile", mod_sf)
sys.modules.setdefault("SPIRAL_OS", types.ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_engine", types.ModuleType("qnl_engine"))
sys.modules.setdefault("SPIRAL_OS.symbolic_parser", types.ModuleType("symbolic_parser"))
sys.modules.setdefault("SPIRAL_OS.qnl_utils", types.ModuleType("qnl_utils"))
sys.modules.setdefault("qnl_engine", types.ModuleType("qnl_engine"))
sys.modules.setdefault("symbolic_parser", types.ModuleType("symbolic_parser"))
req_mod = types.ModuleType("requests")
req_mod.post = lambda *a, **k: types.SimpleNamespace(json=lambda: {}, text="", raise_for_status=lambda: None)
req_mod.RequestException = Exception
sys.modules.setdefault("requests", req_mod)
srv_mod = types.ModuleType("server")
srv_mod.app = object()
sys.modules.setdefault("server", srv_mod)
sys.modules.setdefault("uvicorn", types.ModuleType("uvicorn"))
wc_mod = types.ModuleType("webrtc_connector")
wc_mod.router = None
wc_mod.start_call = lambda *a, **k: None
wc_mod.close_peers = lambda: None
sys.modules.setdefault("connectors.webrtc_connector", wc_mod)

start_path = ROOT / "start_spiral_os.py"
loader = SourceFileLoader("start_spiral_os", str(start_path))
spec = importlib.util.spec_from_loader("start_spiral_os", loader)
start_spiral_os = importlib.util.module_from_spec(spec)

import os
os.environ.setdefault("GLM_API_URL", "http://localhost")
os.environ.setdefault("GLM_API_KEY", "key")
os.environ.setdefault("HF_TOKEN", "token")

loader.exec_module(start_spiral_os)
start_spiral_os.reflection_loop.load_thresholds = lambda: {"default": 0.0}


def _run_main(args):
    argv_backup = sys.argv.copy()
    sys.argv = ["start_spiral_os.py"] + args
    try:
        start_spiral_os.main()
    finally:
        sys.argv = argv_backup


def test_system_status_logged(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    stats = {"cpu": 1}
    monkeypatch.setattr(start_spiral_os.system_monitor, "collect_stats", lambda: stats)
    captured = {}
    def fake_add(text, meta):
        captured["text"] = text
        captured["meta"] = meta
    monkeypatch.setattr(start_spiral_os.vector_memory, "add_vector", fake_add)
    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda c: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "display_welcome_message", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_init, "summarize_purpose", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_analyze, "analyze_code", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "suggest_enhancement", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "reflect_existence", lambda: None)
    monkeypatch.setattr(start_spiral_os.self_correction_engine, "adjust", lambda *a, **k: None)
    monkeypatch.setattr(__import__('builtins'), 'input', lambda _="": "")
    _run_main(["--no-server", "--no-reflection"])
    log_file = tmp_path / "logs" / "system_status.json"
    assert log_file.exists()
    assert json.loads(log_file.read_text()) == stats
    assert captured["meta"]["type"] == "system_status"
    assert json.loads(captured["text"]) == stats
