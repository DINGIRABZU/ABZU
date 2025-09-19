"""Tests for start spiral os."""

from __future__ import annotations

import builtins
import importlib.util
import os
import sys
import types
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Stub heavy dependencies
hf_stub = types.ModuleType("huggingface_hub")
hf_stub.HfHubHTTPError = RuntimeError
hf_stub.snapshot_download = lambda *a, **k: ""
hf_stub.hf_hub_download = lambda *a, **k: ""
hf_stub.cached_download = lambda *a, **k: ""
hf_stub.get_session = lambda: types.SimpleNamespace(post=lambda *a, **k: None)
sys.modules["huggingface_hub"] = hf_stub
sys.modules["huggingface_hub.utils"] = hf_stub
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("numpy", types.ModuleType("numpy"))
sys.modules["numpy"].random = types.SimpleNamespace(rand=lambda *a, **k: 0)
sys.modules["numpy"].int16 = "int16"
sys.modules["numpy"].float32 = float
sys.modules["numpy"].ndarray = object
st_mod = types.ModuleType("sentence_transformers")
st_mod.__path__ = []  # treat as package for submodule imports


class _StubSentenceTransformer:
    def __init__(self, *args, **kwargs):  # pragma: no cover - simple stub
        self.args = args
        self.kwargs = kwargs

    def encode(self, inputs, *args, **kwargs):  # pragma: no cover - simple stub
        if isinstance(inputs, str):
            inputs = [inputs]
        return [[0.0 for _ in range(3)] for _ in inputs]


st_util = types.SimpleNamespace(cos_sim=lambda *a, **k: 0.0)
st_mod.SentenceTransformer = _StubSentenceTransformer
st_mod.util = st_util
sys.modules["sentence_transformers"] = st_mod
sys.modules["sentence_transformers.util"] = st_util
if "sentence_transformers" in sys.modules:
    sys.modules["sentence_transformers"].SentenceTransformer = _StubSentenceTransformer
    setattr(sys.modules["sentence_transformers"], "util", st_util)
    sys.modules["sentence_transformers.util"] = st_util
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

from tests.helpers.config_stub import build_settings

config_mod = types.ModuleType("config")
config_mod.settings = build_settings()
config_mod.reload = lambda: None
sys.modules.setdefault("config", config_mod)
rag_pkg = sys.modules.setdefault("rag", types.ModuleType("rag"))
orch_mod = types.ModuleType("rag.orchestrator")
orch_mod.MoGEOrchestrator = lambda *a, **k: types.SimpleNamespace(
    handle_input=lambda self, text: None
)
rag_pkg.orchestrator = orch_mod
sys.modules.setdefault("rag.orchestrator", orch_mod)
tools_mod = types.ModuleType("tools")
reflection_mod = types.ModuleType("reflection_loop")
reflection_mod.load_thresholds = lambda: {"default": 0.0}
reflection_mod.run_reflection_loop = lambda *a, **k: None
tools_mod.reflection_loop = reflection_mod
sys.modules.setdefault("tools", tools_mod)
sys.modules.setdefault("tools.reflection_loop", reflection_mod)
server_mod = types.ModuleType("server")
server_mod.app = object()
sys.modules.setdefault("server", server_mod)
core_mod = types.ModuleType("core")
core_mod.self_correction_engine = types.ModuleType("self_correction_engine")
core_mod.language_engine = types.ModuleType("language_engine")
core_mod.__path__ = []  # treat as package for submodule imports
sys.modules.setdefault("core", core_mod)
sys.modules.setdefault("core.self_correction_engine", core_mod.self_correction_engine)
sys.modules.setdefault("core.language_engine", core_mod.language_engine)
sys.modules.setdefault("core.utils", types.ModuleType("core.utils"))
optional_mod = types.ModuleType("optional_deps")
optional_mod.lazy_import = lambda name: sys.modules.get(name)
sys.modules.setdefault("core.utils.optional_deps", optional_mod)
core_mod.self_correction_engine.adjust = lambda *a, **k: None
neoabzu_mod = types.ModuleType("neoabzu_rag")


class _StubMoGEOrchestrator:
    def __init__(self, *args, **kwargs):  # pragma: no cover - simple stub
        self.args = args
        self.kwargs = kwargs

    def handle_input(self, text):  # pragma: no cover - simple stub
        return {}


neoabzu_mod.MoGEOrchestrator = _StubMoGEOrchestrator
sys.modules.setdefault("neoabzu_rag", neoabzu_mod)
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


@pytest.fixture(autouse=True)
def _mock_listening_engine(monkeypatch):
    """Provide deterministic audio capture and feature extraction."""

    monkeypatch.setitem(sys.modules, "sentence_transformers", st_mod)
    monkeypatch.setitem(sys.modules, "sentence_transformers.util", st_util)
    monkeypatch.setattr(
        getattr(start_spiral_os, "sentence_transformers", st_mod),
        "SentenceTransformer",
        _StubSentenceTransformer,
        raising=False,
    )
    monkeypatch.setattr(
        getattr(start_spiral_os, "sentence_transformers", st_mod),
        "util",
        st_util,
        raising=False,
    )
    monkeypatch.setitem(sys.modules, "huggingface_hub", hf_stub)
    monkeypatch.setitem(sys.modules, "huggingface_hub.utils", hf_stub)
    if getattr(start_spiral_os, "vector_memory", None) is not None:
        monkeypatch.setattr(
            start_spiral_os.vector_memory, "add_vector", lambda *a, **k: None
        )

    class _DummyValidator:
        def validate_text(self, _text: str) -> bool:  # pragma: no cover - simple stub
            return True

    monkeypatch.setattr(start_spiral_os, "EthicalValidator", lambda: _DummyValidator())

    waveform = [0.0, 0.1, -0.1, 0.0]

    def fake_capture(duration, sr=44100):
        return waveform, False

    def fake_extract(audio, sr):
        return {
            "emotion": "neutral",
            "weight": 0.0,
            "classification": "speech",
            "dialect": "neutral",
            "pitch": 0.0,
            "tempo": 0.0,
            "transcript": "synthetic sample",
            "text": "synthetic sample",
            "is_silent": False,
            "intensity": 0.0,
            "sample_rate": sr,
            "sample_count": len(audio),
            "timestamp": "1970-01-01T00:00:00",
        }

    monkeypatch.setattr(start_spiral_os.listening_engine, "capture_audio", fake_capture)
    monkeypatch.setattr(
        start_spiral_os.listening_engine, "_extract_features", fake_extract
    )


def _fake_collect_stats():
    """Return deterministic telemetry for the boot sequence tests."""

    return {
        str(start_spiral_os.glm_init.PURPOSE_FILE): 0,
        str(start_spiral_os.glm_analyze.ANALYSIS_FILE): 0,
        str(start_spiral_os.inanna_ai.SUGGESTIONS_LOG): 0,
        str(Path("network_logs/defensive.pcap")): 0,
    }


start_spiral_os.system_monitor.collect_stats = _fake_collect_stats


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
    monkeypatch.setattr(
        start_spiral_os.inanna_ai,
        "display_welcome_message",
        lambda: events.append("welcome"),
    )
    monkeypatch.setattr(
        start_spiral_os.glm_init,
        "summarize_purpose",
        lambda: events.append("summary") or "sum",
    )
    monkeypatch.setattr(
        start_spiral_os.glm_analyze,
        "analyze_code",
        lambda: events.append("analyze") or "ana",
    )
    monkeypatch.setattr(
        start_spiral_os.inanna_ai,
        "suggest_enhancement",
        lambda: events.append("suggest") or [],
    )
    monkeypatch.setattr(
        start_spiral_os.inanna_ai,
        "reflect_existence",
        lambda: events.append("reflect") or "id",
    )
    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda c: None)

    calls = {}

    def fake_monitor(interface, packet_count=5):
        events.append("network")
        calls["iface"] = interface

    monkeypatch.setattr(start_spiral_os.dnu, "monitor_traffic", fake_monitor)

    class DummyOrch:
        def handle_input(self, text):
            events.append(text)

    monkeypatch.setattr(
        start_spiral_os, "MoGEOrchestrator", lambda *a, **k: DummyOrch()
    )

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
    monkeypatch.setattr(
        start_spiral_os.inanna_ai,
        "display_welcome_message",
        lambda: events.append("welcome"),
    )
    monkeypatch.setattr(
        start_spiral_os.glm_init,
        "summarize_purpose",
        lambda: events.append("summary") or "sum",
    )
    monkeypatch.setattr(
        start_spiral_os.glm_analyze,
        "analyze_code",
        lambda: events.append("analyze") or "ana",
    )
    monkeypatch.setattr(
        start_spiral_os.inanna_ai,
        "suggest_enhancement",
        lambda: events.append("suggest") or [],
    )
    monkeypatch.setattr(
        start_spiral_os.inanna_ai,
        "reflect_existence",
        lambda: events.append("reflect") or "id",
    )
    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda c: None)
    monkeypatch.setattr(
        start_spiral_os.dnu,
        "monitor_traffic",
        lambda interface, packet_count=5: events.append("network"),
    )

    class DummyOrch:
        def handle_input(self, text):
            events.append(text)

    monkeypatch.setattr(
        start_spiral_os, "MoGEOrchestrator", lambda *a, **k: DummyOrch()
    )

    inputs = iter(
        [
            "",
        ]
    )
    monkeypatch.setattr(builtins, "input", lambda _="": next(inputs))

    _run_main(
        [
            "--skip-network",
            "--interface",
            "eth0",
            "--no-server",
            "--no-reflection",
        ]
    )

    assert events == ["welcome", "summary", "analyze", "suggest", "reflect"]


def test_logging_fallback_branch(monkeypatch, caplog):
    monkeypatch.setenv("ARCHETYPE_STATE", "")
    target = (
        start_spiral_os.Path(start_spiral_os.__file__).resolve().parent
        / "logging_config.yaml"
    )
    original_exists = start_spiral_os.Path.exists

    def fake_exists(self):
        if self == target:
            return False
        return original_exists(self)

    monkeypatch.setattr(start_spiral_os.Path, "exists", fake_exists, raising=False)
    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda cfg: None)
    called = {}
    monkeypatch.setattr(
        start_spiral_os.logging,
        "basicConfig",
        lambda **kw: called.setdefault("basic", kw),
    )
    monkeypatch.setattr(start_spiral_os, "vector_memory", None)
    monkeypatch.setattr(start_spiral_os.glm_init, "summarize_purpose", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_analyze, "analyze_code", lambda: None)
    monkeypatch.setattr(
        start_spiral_os.inanna_ai, "display_welcome_message", lambda: None
    )
    monkeypatch.setattr(start_spiral_os.inanna_ai, "suggest_enhancement", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "reflect_existence", lambda: None)
    monkeypatch.setattr(start_spiral_os.dnu, "monitor_traffic", lambda *a, **k: None)
    monkeypatch.setattr(
        start_spiral_os,
        "MoGEOrchestrator",
        lambda *a, **k: types.SimpleNamespace(handle_input=lambda *_a, **_k: None),
    )
    monkeypatch.setattr(builtins, "input", lambda _="": "")

    sentinel_server = types.SimpleNamespace(app=object())
    sentinel_invocation = types.SimpleNamespace(invoke_ritual=lambda *_a, **_k: [])
    monkeypatch.setattr(
        start_spiral_os.boot_diagnostics,
        "run_boot_checks",
        lambda: {
            "logging": object(),
            "emotional_state": object(),
            "server": sentinel_server,
            "invocation_engine": sentinel_invocation,
        },
    )

    with caplog.at_level("WARNING"):
        _run_main(["--skip-network", "--no-server", "--no-reflection"])

    assert "basic" in called
    assert "Vector memory module missing" in caplog.text


def test_command_parsing(monkeypatch):
    monkeypatch.setenv("ARCHETYPE_STATE", "")
    events = []
    monkeypatch.setattr(
        start_spiral_os.inanna_ai, "display_welcome_message", lambda: None
    )
    monkeypatch.setattr(start_spiral_os.glm_init, "summarize_purpose", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_analyze, "analyze_code", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "suggest_enhancement", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "reflect_existence", lambda: None)
    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda c: None)

    class DummyOrch:
        def handle_input(self, text):
            events.append(text)

    monkeypatch.setattr(
        start_spiral_os, "MoGEOrchestrator", lambda *a, **k: DummyOrch()
    )
    monkeypatch.setattr(builtins, "input", lambda _="": "")

    _run_main(["--command", "hello world", "--no-server", "--no-reflection"])

    assert events == ["hello world"]


def test_server_and_reflection_run(monkeypatch):
    monkeypatch.setenv("ARCHETYPE_STATE", "")
    calls = {"server": False, "reflect": 0}

    monkeypatch.setattr(
        start_spiral_os.inanna_ai, "display_welcome_message", lambda: None
    )
    monkeypatch.setattr(start_spiral_os.glm_init, "summarize_purpose", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_analyze, "analyze_code", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "suggest_enhancement", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "reflect_existence", lambda: None)
    monkeypatch.setattr(start_spiral_os.dnu, "monitor_traffic", lambda *a, **k: None)
    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda c: None)

    class DummyOrch:
        def handle_input(self, text):
            return {}

    monkeypatch.setattr(
        start_spiral_os, "MoGEOrchestrator", lambda *a, **k: DummyOrch()
    )
    monkeypatch.setattr(builtins, "input", lambda _="": "")

    def fake_run_reflection_loop():
        calls["reflect"] += 1

    monkeypatch.setattr(
        start_spiral_os.reflection_loop, "run_reflection_loop", fake_run_reflection_loop
    )

    def fake_uvicorn_run(app, host="0.0.0.0", port=8000):
        calls["server"] = True

    monkeypatch.setattr(start_spiral_os.uvicorn, "run", fake_uvicorn_run)

    _run_main([])

    assert calls["server"]
    assert calls["reflect"] > 0


def test_boot_diagnostics_recovery(monkeypatch, caplog):
    monkeypatch.setenv("ARCHETYPE_STATE", "")

    def fake_checks():
        return {
            "logging": object(),
            "emotional_state": object(),
            "server": None,
            "invocation_engine": None,
        }

    monkeypatch.setattr(
        start_spiral_os.boot_diagnostics, "run_boot_checks", fake_checks
    )
    original_import = importlib.import_module

    def fake_import(name, package=None):
        if name == "server":
            raise RuntimeError("server import failed")
        if name == "invocation_engine":
            raise RuntimeError("invocation engine missing")
        return original_import(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import)
    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda cfg: None)
    monkeypatch.setattr(start_spiral_os.glm_init, "summarize_purpose", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_analyze, "analyze_code", lambda: None)
    monkeypatch.setattr(
        start_spiral_os.inanna_ai, "display_welcome_message", lambda: None
    )
    monkeypatch.setattr(start_spiral_os.inanna_ai, "suggest_enhancement", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "reflect_existence", lambda: None)
    monkeypatch.setattr(start_spiral_os.dnu, "monitor_traffic", lambda *a, **k: None)
    monkeypatch.setattr(
        start_spiral_os,
        "MoGEOrchestrator",
        lambda *a, **k: types.SimpleNamespace(handle_input=lambda *_a, **_k: None),
    )
    monkeypatch.setattr(start_spiral_os.uvicorn, "run", lambda *a, **k: None)
    monkeypatch.setattr(builtins, "input", lambda _="": "")

    with caplog.at_level("ERROR"):
        _run_main(["--skip-network", "--no-reflection"])

    assert "Server module unavailable" in caplog.text
    assert "Invocation engine unavailable" in caplog.text
    assert start_spiral_os.invocation_engine is None


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
    monkeypatch.setattr(
        start_spiral_os, "MoGEOrchestrator", lambda *a, **k: DummyOrch()
    )
    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda c: None)
    monkeypatch.setattr(
        start_spiral_os.inanna_ai, "display_welcome_message", lambda: None
    )
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
    monkeypatch.setattr(
        start_spiral_os, "MoGEOrchestrator", lambda *a, **k: DummyOrch()
    )
    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda c: None)
    monkeypatch.setattr(
        start_spiral_os.inanna_ai, "display_welcome_message", lambda: None
    )
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
    monkeypatch.setattr(
        start_spiral_os.inanna_ai, "display_welcome_message", lambda: None
    )
    monkeypatch.setattr(start_spiral_os.glm_init, "summarize_purpose", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_analyze, "analyze_code", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "suggest_enhancement", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "reflect_existence", lambda: None)
    monkeypatch.setattr(start_spiral_os.uvicorn, "run", lambda *a, **k: None)
    monkeypatch.setattr(start_spiral_os.dnu, "monitor_traffic", lambda *a, **k: None)
    monkeypatch.setattr(
        start_spiral_os.reflection_loop, "run_reflection_loop", lambda *a, **k: None
    )

    called = {}
    monkeypatch.setattr(
        start_spiral_os.vector_memory,
        "rewrite_vector",
        lambda i, t: called.setdefault("args", (i, t)),
    )
    import sys as _sys

    monkeypatch.setattr(
        _sys.modules["invocation_engine"],
        "invoke_ritual",
        lambda n: called.setdefault("ritual", n) or [],
    )

    _run_main(["--rewrite-memory", "x", "y"])

    assert called["args"] == ("x", "y")
    assert called["ritual"] == "x"


def test_rewrite_memory_failure(monkeypatch):
    monkeypatch.setenv("ARCHETYPE_STATE", "")
    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda c: None)
    monkeypatch.setattr(
        start_spiral_os.inanna_ai, "display_welcome_message", lambda: None
    )
    monkeypatch.setattr(start_spiral_os.glm_init, "summarize_purpose", lambda: None)
    monkeypatch.setattr(start_spiral_os.glm_analyze, "analyze_code", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "suggest_enhancement", lambda: None)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "reflect_existence", lambda: None)
    monkeypatch.setattr(start_spiral_os.uvicorn, "run", lambda *a, **k: None)
    monkeypatch.setattr(start_spiral_os.dnu, "monitor_traffic", lambda *a, **k: None)
    monkeypatch.setattr(
        start_spiral_os.reflection_loop, "run_reflection_loop", lambda *a, **k: None
    )

    def _fail_rewrite(i, t):
        raise RuntimeError("rewrite failed")

    monkeypatch.setattr(start_spiral_os.vector_memory, "rewrite_vector", _fail_rewrite)
    import sys as _sys

    monkeypatch.setattr(
        _sys.modules["invocation_engine"], "invoke_ritual", lambda n: None
    )

    with pytest.raises(SystemExit):
        _run_main(["--rewrite-memory", "x", "y"])
