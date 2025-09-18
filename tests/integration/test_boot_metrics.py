"""Integration tests for Prometheus boot metrics exports."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import pytest

import tests.conftest as conftest_module

from monitoring.boot_metrics import METRIC_NAMES

conftest_module.allow_test(Path(__file__).resolve())


def test_boot_sequence_exports_prometheus_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    boot_metrics_output: Path,
    parse_prometheus_textfile: Callable[[Path], dict[str, float]],
) -> None:
    """Finalize boot metrics and ensure Prometheus export contains core gauges."""

    from scripts import boot_sequence
    from razar import boot_orchestrator

    data_dir = tmp_path / "data"
    logs_dir = tmp_path / "logs"
    data_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    history_path = logs_dir / "razar_boot_history.json"
    state_path = logs_dir / "razar_state.json"
    long_task_path = logs_dir / "razar_long_task.json"
    alerts_dir = logs_dir / "alerts"

    monkeypatch.setattr(boot_sequence, "DATA_DIR", data_dir)
    monkeypatch.setattr(boot_sequence, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(boot_orchestrator, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(boot_orchestrator, "HISTORY_FILE", history_path)
    monkeypatch.setattr(boot_orchestrator, "STATE_FILE", state_path)
    monkeypatch.setattr(boot_orchestrator, "LONG_TASK_LOG_PATH", long_task_path)
    monkeypatch.setattr(boot_orchestrator, "MONITORING_ALERTS_DIR", alerts_dir)
    monkeypatch.setattr(boot_orchestrator, "_emit_event", lambda *_, **__: None)

    boot_sequence.boot_sequence()

    components = [
        {"name": f"service_{idx}", "success": True, "attempts": 1} for idx in range(20)
    ]
    run_metrics = {"components": components, "timestamp": time.time()}
    failure_counts: dict[str, int] = {}
    history = {"history": []}

    start_time = time.time()
    boot_orchestrator.finalize_metrics(run_metrics, history, failure_counts, start_time)

    assert boot_metrics_output.exists(), "Expected boot_metrics.prom to be written"
    metrics = parse_prometheus_textfile(boot_metrics_output)

    assert metrics[METRIC_NAMES.first_attempt_success] == pytest.approx(20.0)
    assert metrics[METRIC_NAMES.success_rate] == pytest.approx(1.0, rel=1e-6)
    assert metrics[METRIC_NAMES.component_total] == pytest.approx(20.0)
    assert metrics[METRIC_NAMES.component_success_total] == pytest.approx(20.0)
    assert metrics[METRIC_NAMES.retry_total] == pytest.approx(0.0)
    assert metrics[METRIC_NAMES.component_failure_total] == pytest.approx(0.0)

    ratio = (
        metrics[METRIC_NAMES.first_attempt_success]
        / metrics[METRIC_NAMES.component_total]
    )
    assert ratio >= 0.95
