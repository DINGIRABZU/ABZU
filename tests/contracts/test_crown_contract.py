"""Stub coverage for the crown contract handshake evidence.

Grounded in ``docs/contracts/crown.md`` and the ``crown_router`` lineage in
``docs/apsu_migration_matrix.md``, these tests validate fixture structure.
Expand them with live telemetry when the Rust crown stack is available in the
sandbox or hardware environments.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
_STAGE_A_CROWN = (
    _FIXTURES
    / "stage_readiness"
    / "stage_a"
    / "20240101T000500Z-stage_a2_crown_replays"
    / "summary.json"
)


def test_crown_replay_summary_shape() -> None:
    """Ensure the Stage A2 crown replay summary has expected keys."""

    payload = json.loads(_STAGE_A_CROWN.read_text(encoding="utf-8"))
    assert payload["stage"] == "stage_a2_crown_replays"
    assert payload["status"] == "success"
    assert payload["log_dir"].startswith("stage_readiness/stage_a/")


@pytest.mark.skip(
    reason=(
        "environment-limited: requires Neo-APSU crown decider telemetry from "
        "hardware replay"
    )
)
def test_crown_contract_hardware_path_placeholder() -> None:
    """Placeholder until the Rust decider/orchestrator path is wired."""

    pytest.skip("Crown contract validation awaits hardware telemetry replay.")
