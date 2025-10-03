"""Stub coverage for the memory contract evidence.

This module references the narrative in ``docs/contracts/memory.md`` and
the ``memory_store.py`` row of ``docs/apsu_migration_matrix.md``. When the
Neo-APSU bundle is available in CI or hardware, extend these tests to
exercise the real persistence path and telemetry comparisons.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
_STAGE_B_MEMORY = (
    _FIXTURES
    / "stage_readiness"
    / "stage_b"
    / "20240102T000000Z-stage_b1_memory_proof"
    / "summary.json"
)


def test_memory_readiness_summary_shape() -> None:
    """Load the Stage B memory proof summary and assert core fields."""

    payload = json.loads(_STAGE_B_MEMORY.read_text(encoding="utf-8"))
    assert payload["stage"] == "stage_b1_memory_proof"
    assert payload["status"] == "success"
    metrics = payload["metrics"]
    window = metrics["rotation_window"]
    assert {"window_id", "started_at", "expires_at"} <= set(window)
    assert "rotation_summary" in metrics
    assert metrics["heartbeat_expiry"].endswith("Z")


@pytest.mark.skip(
    reason=(
        "environment-limited: requires Neo-APSU memory bundle replay on "
        "gate-runner hardware"
    )
)
def test_memory_contract_hardware_path_placeholder() -> None:
    """Placeholder until hardware-backed Neo-APSU bundle is available."""

    pytest.skip("Hardware memory contract validation deferred to gate-runner.")
