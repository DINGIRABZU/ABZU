"""Memory contract placeholder validations.

Entry point:
    pytest tests/contracts/test_memory_contract.py

Tracks ``docs/contracts/memory.md`` and the ``memory_store.py`` row of
``docs/apsu_migration_matrix.md``. TODO hardware replay when the Neo-APSU
bundle is published for the hardware gate-runner.
"""

from __future__ import annotations

import pytest

from .utils import HARDWARE_TODO_NOTE, load_contract_fixture


def test_memory_readiness_summary_shape() -> None:
    """Load the Stage B memory proof summary and assert core fields."""

    payload = load_contract_fixture(
        "stage_readiness",
        "stage_b",
        "20240102T000000Z-stage_b1_memory_proof",
        "summary.json",
    )
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
        "gate-runner hardware; " + HARDWARE_TODO_NOTE
    )
)
def test_memory_contract_hardware_path_placeholder() -> None:
    """Placeholder until hardware-backed Neo-APSU bundle is available."""

    pytest.skip(
        "TODO hardware replay: memory contract validation deferred to gate-runner."
    )
