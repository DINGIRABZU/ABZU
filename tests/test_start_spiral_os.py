import sys
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
import builtins
import types
import pytest
import os

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Stub heavy dependencies
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
sys.modules.setdefault("psutil", types.ModuleType("psutil"))
pydantic_mod = types.ModuleType("pydantic")
pydantic_mod.BaseSettings = object
pydantic_mod.Field = lambda *a, **k: None
pydantic_mod.AnyHttpUrl = str
sys.modules.setdefault("pydantic", pydantic_mod)
config_mod = types.ModuleType("config")
config_mod.settings = types.SimpleNamespace(vector_db_path="/tmp")
sys.modules.setdefault("config", config_mod)
orch_mod = types.ModuleType("orchestrator")
orch_mod.MoGEOrchestrator = lambda *a, **k: types.SimpleNamespace(handle_input=lambda self, text: None)
sys.modules.setdefault("orchestrator", orch_mod)
tools_mod = types.ModuleType("tools")
reflection_mod = types.ModuleType("reflection_loop")
reflection_mod.load_thresholds = lambda: {"default": 0.0}
reflection_mod.run_reflection_loop = lambda *a, **k: None
tools_mod.reflection_loop = reflection_mod
sys.modules.setdefault("tools", tools_mod)
sys.modules.setdefault("tools.reflection_loop", reflection_mod)
sys.modules.setdefault("server", types.ModuleType("server"))
core_mod = types.ModuleType("core")
core_mod.self_correction_engine = types.ModuleType("self_correction_engine")
core_mod.language_engine = types.ModuleType("language_engine")
sys.modules.setdefault("core", core_mod)
sys.modules.setdefault("core.self_correction_engine", core_mod.self_correction_engine)
sys.modules.setdefault("core.language_engine", core_mod.language_engine)
connectors_mod = types.ModuleType("connectors")
webrtc_mod = types.ModuleType("webrtc_connector")
webrtc_mod.router = object()
webrtc_mod.start_call = lambda *a, **k: None
webrtc_mod.close_peers = lambda *a, **k: None
connectors_mod.webrtc_connector = webrtc_mod
sys.modules.setdefault("connectors", connectors_mod)
sys.modules.setdefault("connectors.webrtc_connector", webrtc_mod)
os.environ.setdefault("GLM_API_URL", "dummy")
os.environ.setdefault("GLM_API_KEY", "dummy")
os.environ.setdefault("HF_TOKEN", "dummy")

start_path = ROOT / "start_spiral_os.py"
loader = SourceFileLoader("start_spiral_os", str(start_path))
spec = importlib.util.spec_from_loader("start_spiral_os", loader)
start_spiral_os = importlib.util.module_from_spec(spec)
loader.exec_module(start_spiral_os)
start_spiral_os.reflection_loop.load_thresholds = lambda: {"default": 0.0}


def _run_main(args):
    argv_backup = sys.argv.copy()
    sys.argv = ["start_spiral_os.py"] + args
    try:
        start_spiral_os.main()
    finally:
        sys.argv = argv_backup


def test_sequence_with_network(monkeypatch):
    monkeypatch.setenv("ARCHETYPE_STATE", "")
    events = []
    monkeypatch.setattr(start_spiral_os.inanna_ai, "display_welcome_message", lambda: events.append("welcome"))
    monkeypatch.setattr(start_spiral_os.glm_init, "summarize_purpose", lambda: events.append("summary") or "sum")
    monkeypatch.setattr(start_spiral_os.glm_analyze, "analyze_code", lambda: events.append("analyze") or "ana")
    monkeypatch.setattr(start_spiral_os.inanna_ai, "suggest_enhancement", lambda: events.append("suggest") or [])
    monkeypatch.setattr(start_spiral_os.inanna_ai, "reflect_existence", lambda: events.append("reflect") or "id")
    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda c: None)

    calls = {}
    def fake_monitor(interface, packet_count=5):
        events.append("network")
        calls["iface"] = interface
    monkeypatch.setattr(start_spiral_os.dnu, "monitor_traffic", fake_monitor)

    class DummyOrch:
        def handle_input(self, text):
            events.append(text)

    monkeypatch.setattr(start_spiral_os, "MoGEOrchestrator", lambda *a, **k: DummyOrch())

    inputs = iter(["hi", ""])
    monkeypatch.setattr(builtins, "input", lambda _="": next(inputs))

    _run_main(["--interface", "eth0", "--no-server", "--no-reflection"])

    assert events == [
        "welcome",
        "summary",
        "analyze",
        "suggest",
        "reflect",
        "hi",
        "network",
    ]
    assert calls["iface"] == "eth0"


def test_sequence_skip_network(monkeypatch):
    monkeypatch.setenv("ARCHETYPE_STATE", "")
    events = []
    monkeypatch.setattr(start_spiral_os.inanna_ai, "display_welcome_message", lambda: events.append("welcome"))
    monkeypatch.setattr(start_spiral_os.glm_init, "summarize_purpose", lambda: events.append("summary") or "sum")
    monkeypatch.setattr(start_spiral_os.glm_analyze, "analyze_code", lambda: events.append("analyze") or "ana")
    monkeypatch.setattr(start_spiral_os.inanna_ai, "suggest_enhancement", lambda: events.append("suggest") or [])
    monkeypatch.setattr(start_spiral_os.inanna_ai, "reflect_existence", lambda: events.append("reflect") or "id")
    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda c: None)
    monkeypatch.setattr(start_spiral_os.dnu, "monitor_traffic", lambda interface, packet_count=5: events.append("network"))

    class DummyOrch:
        def handle_input(self, text):
            events.append(text)

    monkeypatch.setattr(start_spiral_os, "MoGEOrchestrator", lambda *a, **k: DummyOrch())

    inputs = iter(["",])
    monkeypatch.setattr(builtins, "input", lambda _="": next(inputs))

    _run_main([
        "--skip-network",
        "--interface",
        "eth0",
        "--no-server",
        "--no-reflection",
    ])

    assert events == ["welcome", "summary", "analyze", "suggest", "reflect"]


def test_command_parsing(monkeypatch):
    monkeypatch.setenv("ARCHETYPE_STATE", "")
    events = []
    monkeypatch.setattr(start_spiral_os.inanna_ai, "display_welcome_message", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_init, "summarize_purpose", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_analyze, "analyze_code", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "suggest_enhancement", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "reflect_existence", lambda: None)
    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda c: None)

    class DummyOrch:
        def handle_input(self, text):
            events.append(text)

    monkeypatch.setattr(start_spiral_os, "MoGEOrchestrator", lambda *a, **k: DummyOrch())
    monkeypatch.setattr(builtins, "input", lambda _="": "")

    _run_main(["--command", "hello world", "--no-server", "--no-reflection"])

    assert events == ["hello world"]


def test_server_and_reflection_run(monkeypatch):
    monkeypatch.setenv("ARCHETYPE_STATE", "")
    calls = {"server": False, "reflect": 0}

    monkeypatch.setattr(start_spiral_os.inanna_ai, "display_welcome_message", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_init, "summarize_purpose", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_analyze, "analyze_code", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "suggest_enhancement", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "reflect_existence", lambda: None)
    monkeypatch.setattr(start_spiral_os.dnu, "monitor_traffic", lambda *a, **k: None)
    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda c: None)

    class DummyOrch:
        def handle_input(self, text):
            return {}

    monkeypatch.setattr(start_spiral_os, "MoGEOrchestrator", lambda *a, **k: DummyOrch())
    monkeypatch.setattr(builtins, "input", lambda _="": "")

    def fake_run_reflection_loop():
        calls["reflect"] += 1

    monkeypatch.setattr(start_spiral_os.reflection_loop, "run_reflection_loop", fake_run_reflection_loop)

    def fake_uvicorn_run(app, host="0.0.0.0", port=8000):
        calls["server"] = True

    monkeypatch.setattr(start_spiral_os.uvicorn, "run", fake_uvicorn_run)

    _run_main([])

    assert calls["server"]
    assert calls["reflect"] > 0


def test_validator_blocks_prompt(monkeypatch):
    monkeypatch.setenv("ARCHETYPE_STATE", "")
    events = []

    class DummyValidator:
        def validate_text(self, text):
            events.append(f"val:{text}")
            return "banned" not in text

    class DummyOrch:
        def handle_input(self, text):
            events.append(f"orch:{text}")

    monkeypatch.setattr(start_spiral_os, "EthicalValidator", lambda: DummyValidator())
    monkeypatch.setattr(start_spiral_os, "MoGEOrchestrator", lambda *a, **k: DummyOrch())
    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda c: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "display_welcome_message", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_init, "summarize_purpose", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_analyze, "analyze_code", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "suggest_enhancement", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "reflect_existence", lambda: None)

    inputs = iter(["banned words", "clean", ""]) 
    monkeypatch.setattr(builtins, "input", lambda _="": next(inputs))

    _run_main(["--no-server", "--no-reflection"])

    assert events == ["val:banned words", "val:clean", "orch:clean"]


def test_no_validator_option(monkeypatch):
    monkeypatch.setenv("ARCHETYPE_STATE", "")
    events = []

    class DummyValidator:
        def validate_text(self, text):
            events.append(f"val:{text}")
            return False

    class DummyOrch:
        def handle_input(self, text):
            events.append(f"orch:{text}")

    monkeypatch.setattr(start_spiral_os, "EthicalValidator", lambda: DummyValidator())
    monkeypatch.setattr(start_spiral_os, "MoGEOrchestrator", lambda *a, **k: DummyOrch())
    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda c: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "display_welcome_message", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_init, "summarize_purpose", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_analyze, "analyze_code", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "suggest_enhancement", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "reflect_existence", lambda: None)

    inputs = iter(["bad", ""])
    monkeypatch.setattr(builtins, "input", lambda _="": next(inputs))

    _run_main(["--no-validator", "--no-server", "--no-reflection"])

    assert events == ["orch:bad"]


def test_rewrite_memory_option(monkeypatch):
    monkeypatch.setenv("ARCHETYPE_STATE", "")
    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda c: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "display_welcome_message", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_init, "summarize_purpose", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_analyze, "analyze_code", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "suggest_enhancement", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "reflect_existence", lambda: None)
    monkeypatch.setattr(start_spiral_os.uvicorn, "run", lambda *a, **k: None)
    monkeypatch.setattr(start_spiral_os.dnu, "monitor_traffic", lambda *a, **k: None)
    monkeypatch.setattr(start_spiral_os.reflection_loop, "run_reflection_loop", lambda *a, **k: None)

    called = {}
    monkeypatch.setattr(
        start_spiral_os.vector_memory,
        "rewrite_vector",
        lambda i, t: called.setdefault("args", (i, t)),
    )
    import sys as _sys
    monkeypatch.setattr(_sys.modules['invocation_engine'], "invoke_ritual", lambda n: called.setdefault("ritual", n) or [])

    _run_main(["--rewrite-memory", "x", "y"])

    assert called["args"] == ("x", "y")
    assert called["ritual"] == "x"


def test_rewrite_memory_failure(monkeypatch):
    monkeypatch.setenv("ARCHETYPE_STATE", "")
    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda c: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "display_welcome_message", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_init, "summarize_purpose", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_analyze, "analyze_code", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "suggest_enhancement", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "reflect_existence", lambda: None)
    monkeypatch.setattr(start_spiral_os.uvicorn, "run", lambda *a, **k: None)
    monkeypatch.setattr(start_spiral_os.dnu, "monitor_traffic", lambda *a, **k: None)
    monkeypatch.setattr(start_spiral_os.reflection_loop, "run_reflection_loop", lambda *a, **k: None)

    def _fail_rewrite(i, t):
        raise RuntimeError("rewrite failed")

    monkeypatch.setattr(start_spiral_os.vector_memory, "rewrite_vector", _fail_rewrite)
    import sys as _sys
    monkeypatch.setattr(_sys.modules['invocation_engine'], "invoke_ritual", lambda n: None)

    with pytest.raises(SystemExit):
        _run_main(["--rewrite-memory", "x", "y"])

