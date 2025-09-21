"""Tests for the Stage B rehearsal scheduler helpers."""

from pathlib import Path

from tests import conftest as conftest_module

conftest_module.ALLOWED_TESTS.update(
    {str(Path(__file__).resolve()), str(Path(__file__))}
)

from scripts.rehearsal_scheduler import (
    extract_new_rotation_entries,
    render_prometheus_metrics,
)


def test_extract_new_rotation_entries_detects_new_records() -> None:
    previous = [
        {
            "connector_id": "operator_api",
            "rotated_at": "2024-01-01T00:00:00Z",
            "window_hours": 48,
        }
    ]
    current = previous + [
        {
            "connector_id": "operator_upload",
            "rotated_at": "2024-01-01T06:00:00Z",
            "window_hours": 48,
        },
        {
            "connector_id": "operator_api",
            "rotated_at": "2024-01-02T00:00:00Z",
            "window_hours": 48,
        },
    ]

    new_entries = extract_new_rotation_entries(previous, current)

    assert len(new_entries) == 2
    ids = {entry["connector_id"] for entry in new_entries}
    assert ids == {"operator_upload", "operator_api"}


def test_render_prometheus_metrics_emits_expected_lines() -> None:
    summary = {
        "overall_ok": True,
        "health_checks": {
            "ok": True,
            "results": [
                {"name": "operator_api", "ok": True, "kind": "connector"},
                {"name": "kimi2", "ok": False, "kind": "remote"},
            ],
        },
        "stage_b_smoke": {"ok": True, "doctrine_ok": True},
        "rotation_drills": {
            "ok": True,
            "total_entries": 5,
            "new_entries": [{"connector_id": "operator_api"}],
            "missing": ["operator_upload"],
            "expected": ["operator_api", "operator_upload"],
        },
    }

    prom = render_prometheus_metrics(summary)

    assert "stage_b_rehearsal_run_status 1" in prom
    assert (
        'stage_b_rehearsal_health_check{target="operator_api",kind="connector"} 1'
        in prom
    )
    assert 'stage_b_rehearsal_health_check{target="kimi2",kind="remote"} 0' in prom
    assert "stage_b_rehearsal_stage_b_smoke_success 1" in prom
    assert "stage_b_rehearsal_rotation_entries_total 5" in prom
    assert 'stage_b_rehearsal_rotation_entry{connector_id="operator_upload"} 0' in prom
