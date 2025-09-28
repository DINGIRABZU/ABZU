"""Pytest configuration and shared fixtures."""

from __future__ import annotations

# mypy: ignore-errors
__version__ = "0.0.1"

ALLOWED_TESTS: set[str] = set()
__all__ = ["ALLOWED_TESTS", "allow_test", "allow_tests"]

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

# Path to the minimal boot configuration used in tests
from scripts.boot_sequence import BOOT_CONFIG_PATH

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


def allow_test(test_path: str | Path) -> None:
    """Safely append a test path to the ALLOWED_TESTS set."""
    path = Path(test_path)
    if not path.is_absolute():
        path = ROOT / path
    ALLOWED_TESTS.add(str(path))


def allow_tests(*test_paths: str | Path) -> None:
    """Allow multiple tests by updating ``ALLOWED_TESTS`` safely."""
    for test_path in test_paths:
        allow_test(test_path)


@pytest.fixture(scope="session")
def boot_config_path() -> Path:
    """Location of the minimal boot configuration."""
    return BOOT_CONFIG_PATH


@pytest.fixture
def boot_metrics_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect Prometheus boot metrics to a temporary path for tests."""

    from monitoring import boot_metrics

    output = tmp_path / "monitoring" / "boot_metrics.prom"
    monkeypatch.setattr(boot_metrics, "BOOT_METRICS_PATH", output)
    return output


@pytest.fixture
def parse_prometheus_textfile():
    """Return a helper that parses Prometheus textfiles into a dictionary."""

    from prometheus_client.parser import text_string_to_metric_families

    def _parse(path: Path) -> dict[str, float]:
        metrics: dict[str, float] = {}
        if not path.exists():
            return metrics
        content = path.read_text(encoding="utf-8")
        for family in text_string_to_metric_families(content):
            for sample in family.samples:
                metrics[sample.name] = float(sample.value)
        return metrics

    return _parse


@pytest.fixture
def crown_replay_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> dict[str, Path]:
    """Provide deterministic stubs for Crown replay regression."""

    import crown_prompt_orchestrator as cpo
    import memory.sacred as sacred
    from tools import session_logger

    def _deterministic_glyph(inputs: dict[str, object]) -> tuple[Path, str]:
        payload = json.dumps(inputs, sort_keys=True)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return Path(f"crown_glyphs/{digest[:16]}.png"), f"Glyph hash {digest[:12]}"

    audio_dir = tmp_path / "audio"
    video_dir = tmp_path / "video"
    audio_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(cpo, "record_task_flow", lambda *a, **k: None)
    monkeypatch.setattr(cpo, "review_test_outcomes", lambda *a, **k: [])

    def _stable_spiral(prompt: str) -> str:
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        return f"{prompt}\n<spiral:{digest[:16]}>"

    monkeypatch.setattr(cpo, "spiral_recall", _stable_spiral)
    monkeypatch.setattr(sacred, "generate_sacred_glyph", _deterministic_glyph)
    monkeypatch.setattr(cpo, "generate_sacred_glyph", _deterministic_glyph)
    monkeypatch.setattr(session_logger, "AUDIO_DIR", audio_dir)
    monkeypatch.setattr(session_logger, "VIDEO_DIR", video_dir)

    return {"audio_dir": audio_dir, "video_dir": video_dir}


# Skip tests that rely on unavailable heavy resources unless explicitly allowed
allow_tests(
    ROOT / "tests" / "connectors" / "test_connector_heartbeat.py",
    ROOT / "tests" / "communication" / "test_mcp_fallback.py",
    ROOT / "tests" / "test_adaptive_learning_stub.py",
    ROOT / "tests" / "test_env_validation.py",
    ROOT / "tests" / "crown" / "test_config.py",
    ROOT / "tests" / "crown" / "test_replay_determinism.py",
    ROOT / "tests" / "test_download_deepseek.py",
    ROOT / "tests" / "test_dashboard_app.py",
    ROOT / "tests" / "test_feedback_logging_import.py",
    ROOT / "tests" / "test_dashboard_usage.py",
    ROOT / "tests" / "test_virtual_env_manager.py",
    ROOT / "tests" / "test_sandbox_session.py",
    ROOT / "tests" / "test_dependency_installer.py",
    ROOT / "tests" / "test_start_spiral_os.py",
    ROOT / "tests" / "test_spiral_os.py",
    ROOT / "tests" / "integration" / "test_razar_failover.py",
    ROOT / "tests" / "test_spiral_memory.py",
    ROOT / "tests" / "test_vector_memory.py",
    ROOT / "tests" / "test_vector_memory_extensions.py",
    ROOT / "tests" / "test_vector_memory_persistence.py",
    ROOT / "tests" / "test_vector_memory_scaling.py",
    ROOT / "tests" / "test_spiral_vector_db.py",
    ROOT / "tests" / "test_chat2db_integration.py",
    ROOT / "tests" / "test_corpus_memory.py",
    ROOT / "tests" / "INANNA_AI" / "test_origin_ingestion.py",
    ROOT / "tests" / "test_bootstrap.py",
    ROOT / "tests" / "test_avatar_lipsync.py",
    ROOT / "tests" / "agents" / "nazarick" / "test_resuscitator_flow.py",
    ROOT / "tests" / "agents" / "nazarick" / "test_chakra_resuscitator.py",
    ROOT / "tests" / "test_boot_sequence.py",
    ROOT / "tests" / "test_lip_sync.py",
    ROOT / "tests" / "test_memory_search.py",
    ROOT / "tests" / "test_memory_persistence.py",
    ROOT / "tests" / "web_operator" / "test_arcade_flow.py",
    ROOT / "tests" / "web_console" / "test_chakra_pulse_panel.py",
    ROOT / "tests" / "heart" / "memory_emotional" / "test_memory_emotional.py",
    ROOT / "tests" / "test_start_dev_agents_triage.py",
    ROOT / "tests" / "test_gateway.py",
    ROOT / "tests" / "test_core_scipy_smoke.py",
    ROOT / "tests" / "test_download_models.py",
    ROOT / "tests" / "test_servant_download.py",
    ROOT / "tests" / "test_download_model.py",
    ROOT / "tests" / "test_api_endpoints.py",
    ROOT / "tests" / "test_style_selection.py",
    ROOT / "tests" / "test_prompt_engineering.py",
    ROOT / "tests" / "test_model.py",
    ROOT / "tests" / "test_logging_filters.py",
    ROOT / "tests" / "test_rag_engine.py",
    ROOT / "tests" / "test_data_pipeline.py",
    ROOT / "tests" / "test_deployment_configs.py",
    ROOT / "tests" / "test_memory_snapshot.py",
    ROOT / "tests" / "web_console" / "test_arcade_ui.py",
    ROOT / "tests" / "performance" / "test_task_parser_performance.py",
    ROOT / "tests" / "performance" / "test_vector_memory_performance.py",
    ROOT / "tests" / "performance" / "test_razar_latency.py",
    ROOT / "tests" / "test_auto_retrain.py",
    ROOT / "tests" / "test_autoretrain_full.py",
    ROOT / "tests" / "test_learning_mutator.py",
    ROOT / "tests" / "crown" / "server" / "test_server.py",
    ROOT / "tests" / "test_openwebui_state_updates.py",
    ROOT / "tests" / "test_opencv_import.py",
    ROOT / "tests" / "test_server_endpoints.py",
    ROOT / "tests" / "test_insight_compiler.py",
    ROOT / "tests" / "test_glm_command.py",
    ROOT / "tests" / "test_media_audio.py",
    ROOT / "tests" / "test_audio_backends.py",
    ROOT / "tests" / "test_audio_segment.py",
    ROOT / "tests" / "chakracon" / "test_api.py",
    ROOT / "tests" / "test_video_stream_helpers.py",
    ROOT / "tests" / "test_media_video.py",
    ROOT / "tests" / "test_media_avatar.py",
    ROOT / "tests" / "test_introspection_api.py",
    ROOT / "tests" / "test_lwm.py",
    ROOT / "tests" / "test_emotional_state_logging.py",
    ROOT / "tests" / "test_emotion_state.py",
    ROOT / "tests" / "test_orchestrator.py",
    ROOT / "tests" / "test_play_ritual_music_smoke.py",
    ROOT / "tests" / "test_play_ritual_music.py",
    ROOT / "tests" / "test_bana_narrative_engine.py",
    ROOT / "tests" / "test_mix_tracks_emotion.py",
    ROOT / "tests" / "test_sonic_emotion_mapper.py",
    ROOT / "tests" / "test_transformation_smoke.py",
    ROOT / "tests" / "test_hex_to_glyphs_smoke.py",
    ROOT / "tests" / "test_interactions_jsonl.py",
    ROOT / "tests" / "test_interactions_jsonl_integrity.py",
    ROOT / "tests" / "test_corpus_memory_logging.py",
    ROOT / "tests" / "test_logging_config_rotation.py",
    ROOT / "tests" / "test_music_generation.py",
    ROOT / "tests" / "test_music_generation_emotion.py",
    ROOT / "tests" / "test_music_generation_streaming.py",
    ROOT / "tests" / "test_music_backends_missing.py",
    ROOT / "tests" / "test_music_generation_invocation.py",
    ROOT / "tests" / "test_music_llm_interface_prompt.py",
    ROOT / "tests" / "test_albedo_state_machine.py",
    ROOT / "tests" / "test_albedo_trust.py",
    ROOT / "tests" / "test_vector_memory_extensions.py",
    ROOT / "tests" / "test_cortex_memory.py",
    ROOT / "tests" / "test_voice_cloner_cli.py",
    ROOT / "tests" / "test_security_canary.py",
    ROOT / "tests" / "test_ai_invoker_credentials.py",
    ROOT / "tests" / "agents" / "test_land_graph_geo_knowledge.py",
    ROOT / "tests" / "agents" / "test_asian_gen.py",
    ROOT / "tests" / "test_orchestration_master.py",
    ROOT / "tests" / "memory" / "test_vector_memory.py",
    ROOT / "tests" / "test_smoke_imports.py",
    ROOT / "tests" / "test_chat2db_integration.py",
    ROOT / "tests" / "agents" / "razar" / "test_ignition_builder.py",
    ROOT / "tests" / "agents" / "razar" / "test_runtime_manager.py",
    ROOT / "tests" / "agents" / "razar" / "test_boot_sequence.py",
    ROOT / "tests" / "agents" / "razar" / "test_module_builder.py",
    ROOT / "tests" / "agents" / "razar" / "test_planning_engine.py",
    ROOT / "tests" / "agents" / "razar" / "test_pytest_runner.py",
    ROOT / "tests" / "agents" / "razar" / "test_ai_invoker.py",
    ROOT / "tests" / "agents" / "razar" / "test_code_repair.py",
    ROOT / "tests" / "agents" / "razar" / "test_servant_launch.py",
    ROOT / "tests" / "memory" / "test_sharded_memory_store.py",
    ROOT / "tests" / "vision" / "test_yoloe_adapter.py",
    ROOT / "tests" / "test_persona_profiles_loader.py",
    ROOT / "tests" / "test_nazarick_messaging.py",
    ROOT / "tests" / "agents" / "nazarick" / "test_ethics_manifesto.py",
    ROOT / "tests" / "agents" / "nazarick" / "test_trust_matrix.py",
    ROOT / "tests" / "agents" / "nazarick" / "test_document_registry.py",
    ROOT / "tests" / "agents" / "nazarick" / "test_experience_replay.py",
    ROOT / "tests" / "agents" / "test_razar_cli.py",
    ROOT / "tests" / "agents" / "test_razar_blueprint_synthesizer.py",
    ROOT / "tests" / "test_citadel_event_producer.py",
    ROOT / "tests" / "test_citadel_event_processor.py",
    ROOT / "tests" / "agents" / "test_event_bus.py",
    ROOT / "tests" / "narrative_engine" / "test_biosignal_pipeline.py",
    ROOT / "tests" / "narrative_engine" / "test_biosignal_transformation.py",
    ROOT / "tests" / "narrative_engine" / "test_ingestion_to_mistral_output.py",
    ROOT / "tests" / "narrative_engine" / "test_ingest_persist_retrieve.py",
    ROOT / "tests" / "narrative_engine" / "test_event_storage.py",
    ROOT / "tests" / "crown" / "test_prompt_orchestrator.py",
    ROOT / "tests" / "agents" / "razar" / "test_boot_orchestrator.py",
    ROOT / "tests" / "agents" / "razar" / "test_ignition_sequence.py",
    ROOT / "tests" / "agents" / "razar" / "test_crown_handshake.py",
    ROOT / "tests" / "agents" / "razar" / "test_mission_brief_rotation.py",
    ROOT / "tests" / "agents" / "razar" / "test_state_validator.py",
    ROOT / "tests" / "test_operator_api.py",
    ROOT / "tests" / "test_operator_command_route.py",
    ROOT / "tests" / "test_operator_transport_contract.py",
    ROOT / "tests" / "ignition" / "test_full_stack.py",
    ROOT / "tests" / "ignition" / "test_validate_ignition_script.py",
    ROOT / "tests" / "bana" / "test_event_structurizer.py",
    ROOT / "tests" / "core" / "test_memory_physical.py",
    ROOT / "tests" / "audio" / "test_mix_tracks.py",
    ROOT / "tests" / "integration" / "test_mix_and_store.py",
    ROOT / "tests" / "test_transformers_generate.py",
    ROOT / "tests" / "razar" / "test_ai_invoker.py",
    ROOT / "tests" / "razar" / "test_long_task.py",
    ROOT / "tests" / "integration" / "test_core_regressions.py",
    ROOT / "tests" / "integration" / "test_full_flows.py",
    ROOT
    / "tests"
    / "integration"
    / "remote_agents"
    / "test_ai_invoker_remote_agents.py",
    ROOT / "tests" / "scripts" / "test_verify_chakra_monitoring.py",
    ROOT / "tests" / "scripts" / "test_verify_doctrine_refs.py",
    ROOT / "tests" / "integration" / "test_boot_metrics.py",
    ROOT / "tests" / "integration" / "test_razar_self_healing.py",
    ROOT / "tests" / "spiral_os" / "test_chakra_cycle.py",
    ROOT / "tests" / "chakra_healing" / "test_root.py",
    ROOT / "tests" / "chakra_healing" / "test_sacral.py",
    ROOT / "tests" / "chakra_healing" / "test_solar.py",
    ROOT / "tests" / "chakra_healing" / "test_heart.py",
    ROOT / "tests" / "chakra_healing" / "test_throat.py",
    ROOT / "tests" / "chakra_healing" / "test_third_eye.py",
    ROOT / "tests" / "chakra_healing" / "test_crown.py",
    ROOT / "tests" / "test_metrics_endpoints.py",
    ROOT / "tests" / "narrative" / "test_self_heal_logging.py",
    ROOT / "tests" / "narrative" / "test_narrative_api.py",
    ROOT / "tests" / "test_config_registry.py",
    ROOT / "tests" / "tools" / "test_opencode_client.py",
    ROOT / "tests" / "razar" / "test_remote_repair.py",
    ROOT / "tests" / "monitoring" / "test_heartbeat_logger.py",
    ROOT / "tests" / "docs" / "test_connector_links.py",
)


import importlib.util
import shutil
import time

import corpus_memory_logging

FAIL_LOG = ROOT / "logs" / "pytest.log"

# Prometheus metrics for test observability
try:  # pragma: no cover - optional dependency
    from prometheus_client import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        write_to_textfile,
    )

    _PROM_REGISTRY = CollectorRegistry()
    _FAILURES = Counter(
        "pytest_test_failures_total",
        "Total test failures",
        registry=_PROM_REGISTRY,
    )
    _PASSES = Counter(
        "pytest_test_passes_total",
        "Total test passes",
        registry=_PROM_REGISTRY,
    )
    _DURATION = Histogram(
        "pytest_test_duration_seconds",
        "Test duration in seconds",
        registry=_PROM_REGISTRY,
    )
    _SESSION_RUNTIME = Gauge(
        "pytest_session_duration_seconds",
        "Total pytest session runtime",
        registry=_PROM_REGISTRY,
    )
    _COVERAGE = Gauge(
        "pytest_coverage_percent",
        "Overall coverage percentage",
        registry=_PROM_REGISTRY,
    )
except Exception:  # pragma: no cover - metrics optional
    _PROM_REGISTRY = None
    _SESSION_RUNTIME = None
    _COVERAGE = None

# Ensure the real SciPy package is loaded before tests potentially stub it.
try:  # pragma: no cover - optional dependency
    import scipy  # noqa: F401
except Exception:  # pragma: no cover - SciPy not installed
    pass

# Provide a minimal `huggingface_hub` stub for tests so that modules depending on
# it can be imported without pulling in the real library. The stub implements the
# small surface area used in the codebase and performs no network operations.
import spiral_os._hf_stub as hf_stub  # noqa: E402

sys.modules.setdefault("huggingface_hub", hf_stub)
sys.modules.setdefault("huggingface_hub.utils", hf_stub)

# Map tests to chakra and component metadata from component_index.json
with open(ROOT / "component_index.json", encoding="utf-8") as f:
    _TEST_META: dict[str, tuple[str, str]] = {}
    for comp in json.load(f).get("components", []):
        chakra = comp.get("chakra")
        comp_id = comp.get("id")
        for test_path in comp.get("tests", []):
            _TEST_META[test_path] = (chakra, comp_id)

spec = importlib.util.spec_from_file_location(
    "seed", ROOT / "src" / "core" / "utils" / "seed.py"
)
seed_module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
assert spec and spec.loader
spec.loader.exec_module(seed_module)  # type: ignore[union-attr]
seed_all = seed_module.seed_all

import pytest  # noqa: E402

# Default to NumPy audio backend unless pydub and ffmpeg are fully available
if "AUDIO_BACKEND" not in os.environ:
    try:  # pragma: no cover - optional dependency

        if shutil.which("ffmpeg") is None:
            raise RuntimeError("ffmpeg not found")
    except Exception:  # pragma: no cover - missing deps
        pass
    else:  # pragma: no cover - deps present
        os.environ["AUDIO_BACKEND"] = "pydub"


import emotion_registry  # noqa: E402
import emotional_state  # noqa: E402

_SESSION_START: float | None = None


@pytest.fixture()
def mock_emotion_state(tmp_path, monkeypatch):
    """Return a temporary emotion state file."""
    state_file = tmp_path / "emotion_state.json"
    monkeypatch.setattr(emotional_state, "STATE_FILE", state_file)
    monkeypatch.setattr(emotion_registry, "STATE_FILE", state_file)
    emotional_state._STATE.clear()
    emotion_registry._STATE.clear()
    emotional_state._save_state()
    emotion_registry._load_state()
    emotional_state.set_last_emotion("longing")
    emotional_state.set_resonance_level(0.75)
    return state_file


@pytest.fixture(autouse=True)
def _seed_all():
    seed = int(os.getenv("PYTEST_SEED", "0"))
    seed_all(seed)


# ---------------------------------------------------------------------------
# Test isolation helpers


def pytest_collectstart(collector):
    """Ensure stubbed ``rag`` modules from other tests do not leak."""
    sys.modules.pop("rag", None)
    sys.modules.pop("rag.orchestrator", None)
    sys.modules.pop("SPIRAL_OS", None)
    sys.modules.pop("SPIRAL_OS.qnl_engine", None)
    sys.modules.pop("SPIRAL_OS.symbolic_parser", None)


def pytest_sessionstart(session):  # pragma: no cover - timing varies
    """Record the session start time for runtime metrics."""
    if _PROM_REGISTRY is not None:
        global _SESSION_START
        _SESSION_START = time.perf_counter()


def pytest_collection_modifyitems(config, items):
    """Annotate tests and skip heavy ones when resources are unavailable."""
    skip_marker = pytest.mark.skip(reason="requires unavailable resources")
    for item in items:
        rel_path = os.path.relpath(str(item.fspath), ROOT).replace(os.sep, "/")
        meta = _TEST_META.get(rel_path)
        if meta:
            chakra, component = meta
            item.add_marker(pytest.mark.chakra(chakra))
            item.add_marker(pytest.mark.component(component))
        if str(item.fspath) not in ALLOWED_TESTS:
            item.add_marker(skip_marker)


def pytest_runtest_logreport(report):  # pragma: no cover - timing varies
    """Record metrics and log failing tests for AI review."""
    if report.when != "call":
        return
    if _PROM_REGISTRY is not None:
        _DURATION.observe(report.duration)
        if report.failed:
            _FAILURES.inc()
        elif report.passed:
            _PASSES.inc()
    if report.failed:
        cov_dir = ROOT / "htmlcov"
        artifacts = [str(cov_dir)] if cov_dir.exists() else None
        corpus_memory_logging.log_test_failure(report.nodeid, FAIL_LOG, artifacts)


if _PROM_REGISTRY is not None:

    def pytest_terminal_summary(
        terminalreporter, exitstatus
    ):  # pragma: no cover - timing varies
        """Finalize Prometheus metrics and write them to disk."""
        try:  # pragma: no cover - coverage optional
            import coverage

            cov = coverage.Coverage(data_file=str(ROOT / ".coverage"))
            cov.load()
            with open(os.devnull, "w") as devnull:
                total = cov.report(file=devnull)
            _COVERAGE.set(total)
        except Exception:  # pragma: no cover - coverage optional
            pass
        if _SESSION_START is not None:
            _SESSION_RUNTIME.set(time.perf_counter() - _SESSION_START)
        metrics_path = ROOT / "monitoring" / "pytest_metrics.prom"
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        write_to_textfile(str(metrics_path), _PROM_REGISTRY)
