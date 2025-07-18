import sys
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
import builtins
import types

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
    monkeypatch.setattr(start_spiral_os.vector_memory, "rewrite_vector", lambda i, t: called.setdefault("args", (i, t)))
    import sys as _sys
    monkeypatch.setattr(_sys.modules['invocation_engine'], "invoke_ritual", lambda n: called.setdefault("ritual", n) or [])

    _run_main(["--rewrite-memory", "x", "y"])

    assert called["args"] == ("x", "y")
    assert called["ritual"] == "x"

