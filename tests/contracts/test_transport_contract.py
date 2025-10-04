"""Transport contract placeholder validations.

Entry point:
    pytest tests/contracts/test_transport_contract.py

Follows ``docs/contracts/transport.md`` and the
``connectors/operator_mcp_adapter.py`` row in ``docs/apsu_migration_matrix.md``.
TODO hardware replay when Stage E telemetry flows on hardware with MCP
credentials restored.
"""

from __future__ import annotations

import pytest

from .utils import HARDWARE_TODO_NOTE, load_contract_fixture


def test_transport_stage_e_fixture_shape() -> None:
    """Validate the Stage E REST parity fixture schema."""

    payload = load_contract_fixture(
        "transport_parity",
        "operator_api_stage_e.json",
    )
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
        "credentials on hardware; " + HARDWARE_TODO_NOTE
    )
)
def test_transport_contract_hardware_path_placeholder() -> None:
    """Placeholder until Stage E REST↔gRPC parity runs on hardware."""

    pytest.skip(
        "TODO hardware replay: transport parity awaits Stage E credential replay."
    )
