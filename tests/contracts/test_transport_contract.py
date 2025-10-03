"""Stub coverage for the transport contract parity evidence.

This module tracks the REST↔gRPC contract detailed in
``docs/contracts/transport.md`` and the
``connectors/operator_mcp_adapter.py`` row in ``docs/apsu_migration_matrix.md``.
Enhance these checks with live connector telemetry once credentials and
hardware access are restored.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
_STAGE_E_REST = _FIXTURES / "transport_parity" / "operator_api_stage_e.json"


def test_transport_stage_e_fixture_shape() -> None:
    """Validate the Stage E REST parity fixture schema."""

    payload = json.loads(_STAGE_E_REST.read_text(encoding="utf-8"))
    assert payload["connector"] == "operator_api"
    assert payload["stage"] == "stage_e"
    responses = payload["responses"]
    assert set(responses) == {"legacy", "neo"}
    legacy_rest = responses["legacy"]["rest"]
    assert {"command_id", "status", "payload", "transport"} <= set(legacy_rest)
    assert legacy_rest["transport"] == "rest"


@pytest.mark.skip(
    reason=(
        "environment-limited: requires Stage E transport replay with MCP "
        "credentials on hardware"
    )
)
def test_transport_contract_hardware_path_placeholder() -> None:
    """Placeholder until Stage E REST↔gRPC parity runs on hardware."""

    pytest.skip("Transport parity requires Stage E hardware credential replay.")
