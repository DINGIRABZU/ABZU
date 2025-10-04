"""Crown contract placeholder validations.

Entry point:
    pytest tests/contracts/test_crown_contract.py

Grounded in ``docs/contracts/crown.md`` and the ``crown_router`` lineage in
``docs/apsu_migration_matrix.md``. TODO hardware replay once the Rust crown
stack emits telemetry from the hardware runner.
"""

from __future__ import annotations

import pytest

from .utils import HARDWARE_TODO_NOTE, load_contract_fixture


def test_crown_replay_summary_shape() -> None:
    """Ensure the Stage A2 crown replay summary has expected keys."""

    payload = load_contract_fixture(
        "stage_readiness",
        "stage_a",
        "20240101T000500Z-stage_a2_crown_replays",
        "summary.json",
    )
    assert payload["stage"] == "stage_a2_crown_replays"
    assert payload["status"] == "success"
    assert payload["log_dir"].startswith("stage_readiness/stage_a/")


@pytest.mark.skip(
    reason=(
        "environment-limited: requires Neo-APSU crown decider telemetry from "
        "hardware replay; " + HARDWARE_TODO_NOTE
    )
)
def test_crown_contract_hardware_path_placeholder() -> None:
    """Placeholder until the Rust decider/orchestrator path is wired."""

    pytest.skip("TODO hardware replay: crown contract validation awaits telemetry.")
