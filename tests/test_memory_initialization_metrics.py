"""Telemetry coverage for MemoryBundle initialization wrappers."""

from __future__ import annotations

import logging
import sys
import types
from pathlib import Path
from typing import Any, Dict, List

import pytest

from tests import conftest as conftest_module

conftest_module.allow_test(Path(__file__).resolve())


class StubBundle:
    """Minimal MemoryBundle stand-in returning predefined statuses."""

    def __init__(self, statuses: Dict[str, str]) -> None:
        self._statuses = dict(statuses)
        self.calls = 0

    def initialize(self) -> Dict[str, str]:
        self.calls += 1
        return dict(self._statuses)


@pytest.fixture
def capture_metrics(monkeypatch: pytest.MonkeyPatch) -> List[Any]:
    """Patch metric exporter to capture emitted values for assertions."""

    captured: List[Any] = []

    def _record(values: Any, *, output_path: Path | None = None) -> None:
        captured.append(values)
        return None

    # Import lazily to avoid circular imports during pytest collection.
    from monitoring import boot_metrics

    monkeypatch.setattr(boot_metrics, "record_memory_init_metrics", _record)
    return captured


def test_boot_orchestrator_memory_metrics(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    capture_metrics: List[Any],
) -> None:
    """`load_rust_components` records metrics and logs duration details."""

    import razar.boot_orchestrator as orchestrator

    bundle = StubBundle({"cortex": "ready", "limbic": "error"})
    monkeypatch.setattr(orchestrator, "_memory_bundle", bundle)
    monkeypatch.setattr(orchestrator, "_core_eval", lambda _: None)
    monkeypatch.setattr(
        orchestrator,
        "record_memory_init_metrics",
        lambda values, *, output_path=None: capture_metrics.append(values),
    )

    with caplog.at_level(logging.INFO):
        orchestrator.load_rust_components()

    assert bundle.calls == 1
    assert capture_metrics, "Expected memory metrics to be captured"
    values = capture_metrics[0]
    assert values.source == "boot_orchestrator"
    assert values.layer_total == pytest.approx(2.0)
    assert values.layer_ready == pytest.approx(1.0)
    assert values.layer_failed == pytest.approx(1.0)
    assert any(
        "Memory bundle initialization via boot_orchestrator" in record.message
        for record in caplog.records
    )
    log_extras = [getattr(record, "memory_layers", None) for record in caplog.records]
    assert any(extra == {"cortex": "ready", "limbic": "error"} for extra in log_extras)


def test_bootstrap_memory_emits_metrics(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    capture_metrics: List[Any],
) -> None:
    """`scripts/bootstrap_memory.main` forwards telemetry to the exporter."""

    fake_rust = types.SimpleNamespace(
        MemoryBundle=lambda: types.SimpleNamespace(initialize=lambda: {"stub": "ok"})
    )
    monkeypatch.setitem(sys.modules, "neoabzu_memory", fake_rust)

    import scripts.bootstrap_memory as bootstrap_memory

    bundle = StubBundle({"cortex": "ready", "limbic": "ready"})
    monkeypatch.setattr(bootstrap_memory, "MemoryBundle", lambda: bundle)
    monkeypatch.setattr(bootstrap_memory.logging, "basicConfig", lambda *_, **__: None)
    monkeypatch.setattr(
        bootstrap_memory,
        "record_memory_init_metrics",
        lambda values, *, output_path=None: capture_metrics.append(values),
    )

    with caplog.at_level(logging.INFO):
        bootstrap_memory.main()

    assert bundle.calls == 1
    assert capture_metrics, "Expected bootstrap_memory metrics to be captured"
    values = capture_metrics[0]
    assert values.source == "bootstrap_memory"
    assert values.layer_total == pytest.approx(2.0)
    assert values.layer_ready == pytest.approx(2.0)
    assert values.layer_failed == pytest.approx(0.0)
    assert any(
        "Memory bundle initialization finished" in record.message
        for record in caplog.records
    )


def test_bootstrap_world_emits_metrics(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    capture_metrics: List[Any],
) -> None:
    """`scripts/bootstrap_world.main` exports telemetry for audits."""

    fake_rust = types.SimpleNamespace(
        MemoryBundle=lambda: types.SimpleNamespace(initialize=lambda: {"stub": "ok"})
    )
    monkeypatch.setitem(sys.modules, "neoabzu_memory", fake_rust)

    import scripts.bootstrap_world as bootstrap_world

    bundle = StubBundle({"cortex": "ready", "limbic": "error"})
    monkeypatch.setattr(bootstrap_world, "MemoryBundle", lambda: bundle)
    monkeypatch.setattr(bootstrap_world, "initialize_crown", lambda: None)
    monkeypatch.setattr(bootstrap_world, "launch_required_agents", lambda: [])
    monkeypatch.setattr(bootstrap_world, "load_manifest", lambda *_: {})
    monkeypatch.setattr(bootstrap_world, "warn_missing_services", lambda *_, **__: None)
    monkeypatch.setattr(bootstrap_world.logging, "basicConfig", lambda *_, **__: None)
    monkeypatch.setattr(
        bootstrap_world,
        "record_memory_init_metrics",
        lambda values, *, output_path=None: capture_metrics.append(values),
    )

    for key in (
        "CORTEX_BACKEND",
        "CORTEX_PATH",
        "EMOTION_BACKEND",
        "EMOTION_DB_PATH",
        "MENTAL_BACKEND",
        "MENTAL_JSON_PATH",
        "SPIRIT_BACKEND",
        "SPIRITUAL_DB_PATH",
        "NARRATIVE_BACKEND",
        "NARRATIVE_LOG_PATH",
        "WORLD_NAME",
    ):
        monkeypatch.setenv(key, f"preset-{key.lower()}")

    with caplog.at_level(logging.INFO):
        bootstrap_world.main()

    assert bundle.calls == 1
    assert capture_metrics, "Expected bootstrap_world metrics to be captured"
    values = capture_metrics[0]
    assert values.source == "bootstrap_world"
    assert values.layer_total == pytest.approx(2.0)
    assert values.layer_ready == pytest.approx(1.0)
    assert values.layer_failed == pytest.approx(1.0)
    assert any(
        "Memory bundle initialization finished" in record.message
        for record in caplog.records
    )
