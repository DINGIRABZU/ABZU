"""Tests for the spiral_os CLI pipeline utility."""

from __future__ import annotations

import asyncio
import builtins
import importlib
import importlib.util
import json
import shlex
import subprocess
import sys
import types
from collections.abc import Coroutine, Iterable
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Any, Tuple

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

spiral_os_path = ROOT / "spiral_os"
loader = SourceFileLoader("spiral_os", str(spiral_os_path))
spec = importlib.util.spec_from_loader("spiral_os", loader)
assert spec is not None
spiral_os = importlib.util.module_from_spec(spec)
loader.exec_module(spiral_os)

from spiral_os import _hf_stub, chakra_cycle, pulse_emitter


@pytest.mark.parametrize("as_str", [True, False])
def test_deploy_pipeline_runs_commands(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, as_str: bool
) -> None:
    # create simple pipeline YAML
    yaml_text = """
steps:
  - name: greet
    run: echo hello
"""
    pipeline = tmp_path / "p.yaml"
    pipeline.write_text(yaml_text)

    calls = []

    def fake_run(cmd: str, **kwargs: Any) -> Any:
        calls.append((cmd, kwargs))

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(spiral_os.subprocess, "run", fake_run)

    path_arg = str(pipeline) if as_str else pipeline
    spiral_os.deploy_pipeline(path_arg)

    cmd, kwargs = calls[0]
    assert cmd.strip().split() == ["echo", "hello"]
    assert kwargs["shell"] is True and kwargs["check"] is True


@pytest.mark.parametrize("as_str", [True, False])
def test_deploy_pipeline_multiline(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, as_str: bool
) -> None:
    yaml_text = """
steps:
  - name: multi
    run: |
      echo hello \
        world
"""
    pipeline = tmp_path / "p.yaml"
    pipeline.write_text(yaml_text)

    calls = []

    def fake_run(cmd: str, **kwargs: Any) -> Any:
        calls.append((cmd, kwargs))

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(spiral_os.subprocess, "run", fake_run)

    path_arg = str(pipeline) if as_str else pipeline
    spiral_os.deploy_pipeline(path_arg)

    cmd, kwargs = calls[0]
    assert cmd.strip().split() == ["echo", "hello", "world"]
    assert kwargs["shell"] is True and kwargs["check"] is True


def test_deploy_pipeline_invalid_yaml(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    pipeline = tmp_path / "p.yaml"
    pipeline.write_text(":: not yaml ::")

    with caplog.at_level("ERROR"):
        with pytest.raises(yaml.YAMLError):
            spiral_os.deploy_pipeline(pipeline)

    assert "Failed to parse pipeline YAML" in caplog.text


def test_deploy_pipeline_command_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    yaml_text = """
steps:
  - run: ok
  - run: bad
"""
    pipeline = tmp_path / "p.yaml"
    pipeline.write_text(yaml_text)

    def fake_run(cmd: str, **kwargs: Any) -> Any:
        if cmd.strip() == "bad":
            raise subprocess.CalledProcessError(1, cmd)

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(spiral_os.subprocess, "run", fake_run)

    with caplog.at_level("ERROR"):
        with pytest.raises(subprocess.CalledProcessError):
            spiral_os.deploy_pipeline(pipeline)

    assert "Command failed" in caplog.text


def test_deploy_pipeline_missing_file(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    missing = tmp_path / "absent.yaml"
    with caplog.at_level("ERROR"):
        with pytest.raises(OSError):
            spiral_os.deploy_pipeline(missing)
    assert "Unable to read pipeline YAML" in caplog.text


def test_cli_main_pipeline_deploy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pipeline = tmp_path / "pipe.yaml"
    pipeline.write_text("steps:\n  - run: echo hi\n")

    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_run(cmd: str, **kwargs: Any) -> Any:
        calls.append((cmd, kwargs))

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(spiral_os.subprocess, "run", fake_run)

    exit_code = spiral_os.main(["pipeline", "deploy", str(pipeline)])
    assert exit_code == 0
    assert calls == [("echo hi", {"shell": True, "check": True})]


def test_cli_main_prints_usage(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = spiral_os.main([])
    out = capsys.readouterr().out
    assert exit_code == 1
    assert out.startswith("usage: spiral_os")


def test_hf_stub_behaviour() -> None:
    assert _hf_stub.snapshot_download("model") == ""
    with pytest.raises(_hf_stub.HfHubHTTPError):
        raise _hf_stub.HfHubHTTPError("boom")


class _DummyStore:
    def __init__(self, state: dict[str, int] | None = None) -> None:
        self.state = state or {"root": 2}
        self.increment_calls: list[str] = []

    def load(self) -> dict[str, int]:
        return dict(self.state)

    def increment(self, chakra: str) -> int:
        self.increment_calls.append(chakra)
        self.state[chakra] = self.state.get(chakra, 0) + 1
        return self.state[chakra]


def test_chakra_cycle_emits_events(monkeypatch: pytest.MonkeyPatch) -> None:
    store = _DummyStore({"root": 5})
    cycle = chakra_cycle.ChakraCycle(store=store, interval=0.0)
    events = cycle.emit_heartbeat()
    chakras = [event.chakra for event in events]
    assert chakras == list(chakra_cycle.GEAR_RATIOS)
    assert store.increment_calls == list(chakra_cycle.GEAR_RATIOS)
    assert cycle.get_cycle("root") == store.state["root"]
    monkeypatch.setattr(chakra_cycle, "_default_cycle", cycle)
    assert chakra_cycle.get_cycle("root") == store.state["root"]
    assert [h.chakra for h in chakra_cycle.emit_heartbeat()] == chakras


def test_chakra_cycle_scheduler_yields() -> None:
    store = _DummyStore()
    cycle = chakra_cycle.ChakraCycle(store=store, interval=0.0)

    async def _consume() -> list[chakra_cycle.Heartbeat]:
        agen = cycle.scheduler()
        try:
            return [await agen.__anext__() for _ in chakra_cycle.GEAR_RATIOS]
        finally:
            await agen.aclose()

    received = asyncio.run(_consume())
    assert {event.chakra for event in received} == set(chakra_cycle.GEAR_RATIOS)


def test_pulse_emitter_broadcast(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[Tuple[str, str, str]] = []

    def fake_emit(source: str, name: str, payload: dict[str, str]) -> None:
        events.append((source, name, payload["chakra"]))
        if len(events) >= 3:
            raise RuntimeError("stop")

    monkeypatch.setattr(pulse_emitter, "emit_event", fake_emit)
    with pytest.raises(RuntimeError):
        asyncio.run(pulse_emitter.emit_pulse(interval=0.0, chakras=["root", "sacral"]))
    assert [evt[2] for evt in events[:2]] == ["root", "sacral"]


def test_pulse_emitter_run_wrapper(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    async def fake_emit(interval: float, chakras: Iterable[str]) -> None:
        captured["params"] = (interval, tuple(chakras))

    def fake_run(coro: Coroutine[Any, Any, Any]) -> None:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(coro)
        finally:
            loop.close()

    monkeypatch.setattr(pulse_emitter, "emit_pulse", fake_emit)
    monkeypatch.setattr(pulse_emitter.asyncio, "run", fake_run)
    pulse_emitter.run(interval=1.5, chakras=["heart"])
    assert captured["params"] == (1.5, ("heart",))


@pytest.fixture()
def pkg_start(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    for key in ("GLM_API_URL", "GLM_API_KEY", "HF_TOKEN"):
        monkeypatch.setenv(key, "token")
    monkeypatch.chdir(tmp_path)

    env_validation = types.ModuleType("env_validation")
    env_validation.check_required = lambda names: None
    env_validation.check_optional_packages = lambda names: None
    monkeypatch.setitem(sys.modules, "env_validation", env_validation)

    emotion_registry = types.ModuleType("emotion_registry")
    layer_changes: list[str] = []

    def set_current_layer(name: str) -> None:
        layer_changes.append(name)

    emotion_registry.set_current_layer = set_current_layer
    emotion_registry.layer_changes = layer_changes
    monkeypatch.setitem(sys.modules, "emotion_registry", emotion_registry)

    emotional_state = types.ModuleType("emotional_state")
    last_emotion: list[str | None] = [None]
    emotional_state.set_last_emotion = lambda value: last_emotion.__setitem__(0, value)
    emotional_state.get_last_emotion = lambda: last_emotion[0]
    monkeypatch.setitem(sys.modules, "emotional_state", emotional_state)

    server = types.ModuleType("server")
    server.app = object()
    monkeypatch.setitem(sys.modules, "server", server)

    archetype = types.ModuleType("archetype_shift_engine")
    archetype.maybe_shift_archetype = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "archetype_shift_engine", archetype)

    connectors = types.ModuleType("connectors")
    webrtc = types.ModuleType("connectors.webrtc_connector")
    webrtc.router = object()
    webrtc.start_call = lambda *a, **k: None
    webrtc.close_peers = lambda *a, **k: None
    connectors.webrtc_connector = webrtc
    monkeypatch.setitem(sys.modules, "connectors", connectors)
    monkeypatch.setitem(sys.modules, "connectors.webrtc_connector", webrtc)

    core = types.ModuleType("core")
    lang_calls: list[Any] = []
    language_engine = types.ModuleType("core.language_engine")
    language_engine.register_connector = lambda connector: lang_calls.append(connector)
    language_engine.calls = lang_calls
    self_engine = types.ModuleType("core.self_correction_engine")
    adjustments: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    self_engine.adjust = lambda *a, **k: adjustments.append((a, k))
    self_engine.adjustments = adjustments
    core.language_engine = language_engine
    core.self_correction_engine = self_engine
    monkeypatch.setitem(sys.modules, "core", core)
    monkeypatch.setitem(sys.modules, "core.language_engine", language_engine)
    monkeypatch.setitem(sys.modules, "core.self_correction_engine", self_engine)

    dashboard = types.ModuleType("dashboard")
    system_stats: list[dict[str, Any]] = []
    system_monitor = types.SimpleNamespace(
        collect_stats=lambda: system_stats.append({"ok": True}) or {"ok": True}
    )
    dashboard.system_monitor = system_monitor
    monkeypatch.setitem(sys.modules, "dashboard", dashboard)
    monkeypatch.setitem(sys.modules, "dashboard.system_monitor", system_monitor)

    def _vector_add(text: str, meta: dict[str, Any]) -> None:
        vector_module.records.append((text, meta))

    vector_module = types.ModuleType("vector_memory")
    vector_module.records = []  # type: ignore[attr-defined]
    vector_module.add_vector = _vector_add
    vector_module.rewrite_vector = lambda *_a, **_k: None
    monkeypatch.setitem(sys.modules, "vector_memory", vector_module)

    invocation_module = types.ModuleType("invocation_engine")
    ritual_calls: list[str] = []

    def _invoke(name: str) -> list[str]:
        ritual_calls.append(name)
        return [f"step:{name}"]

    invocation_module.invoke_ritual = _invoke
    invocation_module.calls = ritual_calls
    monkeypatch.setitem(sys.modules, "invocation_engine", invocation_module)

    uvicorn_mod = types.ModuleType("uvicorn")
    uvicorn_mod.calls: list[tuple[Any, str, int]] = []

    def _uvicorn_run(*, app: Any, host: str, port: int) -> None:
        uvicorn_mod.calls.append((app, host, port))

    uvicorn_mod.run = _uvicorn_run
    monkeypatch.setitem(sys.modules, "uvicorn", uvicorn_mod)

    tools_mod = types.ModuleType("tools")
    reflection_mod = types.ModuleType("tools.reflection_loop")
    reflection_mod.run_reflection_loop = lambda: None
    reflection_mod.load_thresholds = lambda: {"default": 0.5}
    tools_mod.reflection_loop = reflection_mod
    monkeypatch.setitem(sys.modules, "tools", tools_mod)
    monkeypatch.setitem(sys.modules, "tools.reflection_loop", reflection_mod)

    ina_pkg = types.ModuleType("INANNA_AI")
    dnu = types.ModuleType("INANNA_AI.defensive_network_utils")
    dnu.monitor_traffic = lambda *a, **k: None
    glm_init = types.ModuleType("INANNA_AI.glm_init")
    glm_init.PURPOSE_FILE = tmp_path / "purpose.log"
    glm_init.summarize_purpose = lambda: "purpose"
    glm_analyze = types.ModuleType("INANNA_AI.glm_analyze")
    glm_analyze.ANALYSIS_FILE = tmp_path / "analysis.log"
    glm_analyze.analyze_code = lambda: None
    listening_engine = types.ModuleType("INANNA_AI.listening_engine")
    listening_engine.capture_audio = lambda duration: ([0.0], False)
    listening_engine._extract_features = lambda audio, sr: {
        "emotion": "calm",
        "sample_rate": sr,
    }
    ethical_mod = types.ModuleType("INANNA_AI.ethical_validator")

    class _Validator:
        def validate_text(self, text: str) -> bool:
            return True

    ethical_mod.EthicalValidator = _Validator
    personality_mod = types.ModuleType("INANNA_AI.personality_layers")
    personality_mod.REGISTRY = {"albedo": lambda: object()}
    personality_mod.list_personalities = lambda: ["albedo"]
    ina_pkg.defensive_network_utils = dnu
    ina_pkg.glm_init = glm_init
    ina_pkg.glm_analyze = glm_analyze
    ina_pkg.listening_engine = listening_engine
    ina_pkg.ethical_validator = ethical_mod
    ina_pkg.personality_layers = personality_mod
    monkeypatch.setitem(sys.modules, "INANNA_AI", ina_pkg)
    monkeypatch.setitem(sys.modules, "INANNA_AI.defensive_network_utils", dnu)
    monkeypatch.setitem(sys.modules, "INANNA_AI.glm_init", glm_init)
    monkeypatch.setitem(sys.modules, "INANNA_AI.glm_analyze", glm_analyze)
    monkeypatch.setitem(sys.modules, "INANNA_AI.listening_engine", listening_engine)
    monkeypatch.setitem(sys.modules, "INANNA_AI.ethical_validator", ethical_mod)
    monkeypatch.setitem(sys.modules, "INANNA_AI.personality_layers", personality_mod)

    agent_pkg = types.ModuleType("INANNA_AI_AGENT")
    inanna_ai = types.ModuleType("INANNA_AI_AGENT.inanna_ai")
    ai_calls: list[str] = []

    def _welcome() -> None:
        ai_calls.append("welcome")

    def _suggest() -> None:
        ai_calls.append("suggest")

    def _reflect() -> None:
        ai_calls.append("reflect")

    inanna_ai.display_welcome_message = _welcome
    inanna_ai.suggest_enhancement = _suggest
    inanna_ai.reflect_existence = _reflect
    inanna_ai.SUGGESTIONS_LOG = tmp_path / "suggestions.log"
    agent_pkg.inanna_ai = inanna_ai
    monkeypatch.setitem(sys.modules, "INANNA_AI_AGENT", agent_pkg)
    monkeypatch.setitem(sys.modules, "INANNA_AI_AGENT.inanna_ai", inanna_ai)

    neo_pkg = types.ModuleType("neoabzu_rag")

    class _Orchestrator:
        def __init__(self, albedo_layer: Any | None = None) -> None:
            self.albedo_layer = albedo_layer

        def handle_input(self, text: str) -> dict[str, Any]:
            return {"echo": text}

    neo_pkg.MoGEOrchestrator = _Orchestrator
    monkeypatch.setitem(sys.modules, "neoabzu_rag", neo_pkg)

    if "spiral_os.start_spiral_os" in sys.modules:
        del sys.modules["spiral_os.start_spiral_os"]
    module = importlib.import_module("spiral_os.start_spiral_os")
    context = {
        "vector_memory": vector_module,
        "invocation_engine": invocation_module,
        "emotion_registry": emotion_registry,
        "language_engine": language_engine,
        "self_engine": self_engine,
        "uvicorn": uvicorn_mod,
        "ai_calls": ai_calls,
        "system_stats": system_stats,
    }
    return module, context


def test_pkg_start_invoke_ritual(pkg_start, capsys: pytest.CaptureFixture[str]) -> None:
    module, ctx = pkg_start
    module.main(["--invoke-ritual", "alpha"])
    out = capsys.readouterr().out
    assert "step:alpha" in out
    assert ctx["invocation_engine"].calls == ["alpha"]
    assert ctx["vector_memory"].records
    status_path = Path("logs") / "system_status.json"
    assert status_path.exists()
    data = json.loads(status_path.read_text(encoding="utf-8"))
    assert "ok" in data


def test_pkg_start_requires_invocation_engine(pkg_start) -> None:
    module, _ = pkg_start
    module.invocation_engine = None
    with pytest.raises(SystemExit):
        module.main(["--invoke-ritual", "beta"])


@pytest.fixture()
def src_pkg_start(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    for key in ("GLM_API_URL", "GLM_API_KEY", "HF_TOKEN"):
        monkeypatch.setenv(key, "token")
    monkeypatch.chdir(tmp_path)

    env_validation = types.ModuleType("env_validation")
    env_validation.check_required = lambda names: None
    env_validation.check_optional_packages = lambda names: None
    monkeypatch.setitem(sys.modules, "env_validation", env_validation)

    layer_changes: list[str] = []

    def _set_current_layer(name: str) -> None:
        layer_changes.append(name)

    emotion_registry = types.SimpleNamespace(
        layer_changes=layer_changes, set_current_layer=_set_current_layer
    )
    monkeypatch.setitem(sys.modules, "emotion_registry", emotion_registry)

    last_state: list[str | None] = [None]

    def _set_last_emotion(value: str | None) -> None:
        last_state[0] = value

    def _get_last_emotion() -> str | None:
        return last_state[0]

    emotional_state = types.SimpleNamespace(
        last=last_state,
        set_last_emotion=_set_last_emotion,
        get_last_emotion=_get_last_emotion,
    )
    monkeypatch.setitem(sys.modules, "emotional_state", emotional_state)

    server = types.ModuleType("server")
    server.app = object()
    monkeypatch.setitem(sys.modules, "server", server)

    archetype = types.ModuleType("archetype_shift_engine")
    archetype.maybe_shift_archetype = lambda *_a, **_k: None
    monkeypatch.setitem(sys.modules, "archetype_shift_engine", archetype)

    connectors = types.ModuleType("connectors")
    webrtc = types.ModuleType("connectors.webrtc_connector")
    webrtc.router = object()
    webrtc.start_call = lambda *a, **k: None
    webrtc.close_peers = lambda *a, **k: None
    connectors.webrtc_connector = webrtc
    monkeypatch.setitem(sys.modules, "connectors", connectors)
    monkeypatch.setitem(sys.modules, "connectors.webrtc_connector", webrtc)

    core = types.ModuleType("core")
    language_engine = types.ModuleType("core.language_engine")
    language_engine.calls = []

    def _register_connector(connector: Any) -> None:
        language_engine.calls.append(connector)

    language_engine.register_connector = _register_connector
    self_engine = types.ModuleType("core.self_correction_engine")
    self_engine.adjustments = []
    self_engine.adjust = lambda *a, **k: self_engine.adjustments.append((a, k))
    core.language_engine = language_engine
    core.self_correction_engine = self_engine
    monkeypatch.setitem(sys.modules, "core", core)
    monkeypatch.setitem(sys.modules, "core.language_engine", language_engine)
    monkeypatch.setitem(sys.modules, "core.self_correction_engine", self_engine)

    dashboard = types.ModuleType("dashboard")
    system_stats: list[dict[str, Any]] = []

    def _collect_stats() -> dict[str, bool]:
        system_stats.append({"ok": True})
        return {"ok": True}

    system_monitor = types.SimpleNamespace(collect_stats=_collect_stats)
    dashboard.system_monitor = system_monitor
    monkeypatch.setitem(sys.modules, "dashboard", dashboard)
    monkeypatch.setitem(sys.modules, "dashboard.system_monitor", system_monitor)

    vector_module = types.ModuleType("vector_memory")
    vector_module.records = []  # type: ignore[attr-defined]

    def _vector_add(text: str, meta: dict[str, Any]) -> None:
        vector_module.records.append((text, meta))

    vector_module.add_vector = _vector_add
    vector_module.rewrite_vector = lambda *_a, **_k: None
    monkeypatch.setitem(sys.modules, "vector_memory", vector_module)

    invocation_module = types.ModuleType("invocation_engine")
    invocation_module.calls: list[str] = []

    def _invoke(name: str) -> list[str]:
        invocation_module.calls.append(name)
        return [f"step:{name}"]

    invocation_module.invoke_ritual = _invoke
    monkeypatch.setitem(sys.modules, "invocation_engine", invocation_module)

    uvicorn_mod = types.ModuleType("uvicorn")
    uvicorn_mod.calls: list[tuple[Any, str, int]] = []

    def _run_uvicorn(*, app: Any, host: str, port: int) -> None:
        uvicorn_mod.calls.append((app, host, port))

    uvicorn_mod.run = _run_uvicorn
    monkeypatch.setitem(sys.modules, "uvicorn", uvicorn_mod)

    tools_mod = types.ModuleType("tools")
    reflection_mod = types.ModuleType("tools.reflection_loop")
    reflection_mod.run_reflection_loop = lambda: None
    reflection_mod.load_thresholds = lambda: {"default": 0.5}
    tools_mod.reflection_loop = reflection_mod
    monkeypatch.setitem(sys.modules, "tools", tools_mod)
    monkeypatch.setitem(sys.modules, "tools.reflection_loop", reflection_mod)

    ina_pkg = types.ModuleType("INANNA_AI")
    dnu = types.ModuleType("INANNA_AI.defensive_network_utils")
    dnu.monitor_traffic = lambda *a, **k: None
    glm_init = types.ModuleType("INANNA_AI.glm_init")
    glm_init.PURPOSE_FILE = tmp_path / "purpose.log"
    glm_init.summarize_purpose = lambda: "purpose"
    glm_analyze = types.ModuleType("INANNA_AI.glm_analyze")
    glm_analyze.ANALYSIS_FILE = tmp_path / "analysis.log"
    glm_analyze.analyze_code = lambda: None
    listening_engine = types.ModuleType("INANNA_AI.listening_engine")
    listening_engine.capture_audio = lambda duration: ([0.0], False)
    listening_engine._extract_features = lambda audio, sr: {
        "emotion": "calm",
        "sample_rate": sr,
    }
    ethical_mod = types.ModuleType("INANNA_AI.ethical_validator")

    class _Validator:
        def validate_text(self, text: str) -> bool:
            return "block" not in text

    ethical_mod.EthicalValidator = _Validator
    personality_mod = types.ModuleType("INANNA_AI.personality_layers")
    personality_mod.REGISTRY = {
        "albedo": lambda: object(),
        "alias_layer": lambda: object(),
    }
    personality_mod.list_personalities = lambda: ["albedo"]
    ina_pkg.defensive_network_utils = dnu
    ina_pkg.glm_init = glm_init
    ina_pkg.glm_analyze = glm_analyze
    ina_pkg.listening_engine = listening_engine
    ina_pkg.ethical_validator = ethical_mod
    ina_pkg.personality_layers = personality_mod
    monkeypatch.setitem(sys.modules, "INANNA_AI", ina_pkg)
    monkeypatch.setitem(sys.modules, "INANNA_AI.defensive_network_utils", dnu)
    monkeypatch.setitem(sys.modules, "INANNA_AI.glm_init", glm_init)
    monkeypatch.setitem(sys.modules, "INANNA_AI.glm_analyze", glm_analyze)
    monkeypatch.setitem(sys.modules, "INANNA_AI.listening_engine", listening_engine)
    monkeypatch.setitem(sys.modules, "INANNA_AI.ethical_validator", ethical_mod)
    monkeypatch.setitem(sys.modules, "INANNA_AI.personality_layers", personality_mod)

    agent_pkg = types.ModuleType("INANNA_AI_AGENT")
    inanna_ai = types.ModuleType("INANNA_AI_AGENT.inanna_ai")
    inanna_ai.display_welcome_message = lambda: None
    inanna_ai.suggest_enhancement = lambda: None
    inanna_ai.reflect_existence = lambda: None
    inanna_ai.SUGGESTIONS_LOG = tmp_path / "suggestions.log"
    agent_pkg.inanna_ai = inanna_ai
    monkeypatch.setitem(sys.modules, "INANNA_AI_AGENT", agent_pkg)
    monkeypatch.setitem(sys.modules, "INANNA_AI_AGENT.inanna_ai", inanna_ai)

    neo_pkg = types.ModuleType("neoabzu_rag")

    orch_instances: list[Any] = []

    class _Orchestrator:
        def __init__(self, albedo_layer: Any | None = None) -> None:
            self.albedo_layer = albedo_layer
            self.handled: list[str] = []
            orch_instances.append(self)

        def handle_input(self, text: str) -> dict[str, Any]:
            self.handled.append(text)
            return {"echo": text}

    neo_pkg.MoGEOrchestrator = _Orchestrator
    monkeypatch.setitem(sys.modules, "neoabzu_rag", neo_pkg)

    module_name = "src.spiral_os.start_spiral_os"
    sys.modules.pop(module_name, None)
    module = importlib.import_module(module_name)

    context = {
        "emotion_registry": emotion_registry,
        "language_engine": language_engine,
        "self_engine": self_engine,
        "vector_memory": vector_module,
        "invocation_engine": invocation_module,
        "uvicorn": uvicorn_mod,
        "system_stats": system_stats,
        "orch_instances": orch_instances,
    }
    return module, context


def test_src_start_invoke_ritual(src_pkg_start, capsys: pytest.CaptureFixture[str]):
    module, ctx = src_pkg_start
    module.main(["--invoke-ritual", "sigma"])
    out = capsys.readouterr().out
    assert "step:sigma" in out
    assert ctx["invocation_engine"].calls == ["sigma"]


def test_src_start_rewrite_memory(src_pkg_start):
    module, ctx = src_pkg_start
    module.main(["--rewrite-memory", "alpha", "payload"])
    assert any(
        rec[0] == json.dumps({"ok": True}) for rec in ctx["vector_memory"].records
    )
    assert ctx["invocation_engine"].calls[-1] == "alpha"


def test_src_start_command_loop_with_validator(
    src_pkg_start, monkeypatch: pytest.MonkeyPatch
):
    module, ctx = src_pkg_start
    monkeypatch.setenv("WEB_CONSOLE_API_URL", "https://console.local")
    inputs = iter(["block this", "echo", ""])
    monkeypatch.setattr(builtins, "input", lambda _="": next(inputs))
    module.main(["--command", "seed"])
    # initial command is "seed" then validator blocks "block this" and accepts "echo"
    orch = ctx["orch_instances"][-1]
    assert orch.handled[0] == "seed"
    assert orch.handled[-1] == "echo"
    assert ctx["language_engine"].calls == [module.webrtc_connector]


def test_src_start_personality_alias(src_pkg_start, monkeypatch: pytest.MonkeyPatch):
    module, ctx = src_pkg_start
    module.REGISTRY = {"alias_layer": lambda: object()}
    monkeypatch.setattr(builtins, "input", lambda _="": "")
    module.main(["--personality", "alias"])
    assert ctx["emotion_registry"].layer_changes[0] == "alias_layer"


def test_src_start_keyboard_interrupt(
    src_pkg_start, monkeypatch: pytest.MonkeyPatch, capsys
):
    module, _ = src_pkg_start

    def _interrupt(_="") -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(builtins, "input", _interrupt)
    module.main(["--no-validator"])
    out = capsys.readouterr().out
    assert out.endswith("\n")


def test_src_cli_deploy_pipeline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    module = importlib.import_module("src.spiral_os.__main__")
    yaml_file = tmp_path / "pipe.yaml"
    yaml_file.write_text("steps:\n  - echo hi\n")
    calls: list[list[str]] = []

    def fake_run(cmd, check=True):
        calls.append(cmd if isinstance(cmd, list) else shlex.split(cmd))

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    module.deploy_pipeline(yaml_file)
    assert calls[0] == ["echo", "hi"]


def test_src_cli_deploy_requires_steps(tmp_path: Path):
    module = importlib.import_module("src.spiral_os.__main__")
    yaml_file = tmp_path / "pipe.yaml"
    yaml_file.write_text("{}")
    with pytest.raises(ValueError):
        module.deploy_pipeline(yaml_file)


def test_src_cli_main_dispatch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    module = importlib.import_module("src.spiral_os.__main__")
    yaml_file = tmp_path / "pipe.yaml"
    yaml_file.write_text("steps:\n  - echo hi\n")
    monkeypatch.setattr(module, "deploy_pipeline", lambda path: None)
    start_calls: list[list[str]] = []
    monkeypatch.setattr(module, "start_os", lambda args: start_calls.append(args))
    assert module.main(["pipeline", "deploy", str(yaml_file)]) == 0
    assert module.main(["start", "--", "--flag"]) == 0
    assert start_calls == [["--", "--flag"]]
    assert module.main([]) == 1
