import json
from pathlib import Path
from typing import Any
import asyncio
import importlib.util
import sys
import types

import httpx
import pytest

from tests.conftest import ALLOWED_TESTS, allow_test

allow_test(__file__)
assert str(Path(__file__).resolve()) in ALLOWED_TESTS

ROOT = Path(__file__).resolve().parents[2]
CONNECTORS_DIR = ROOT / "connectors"

connectors_stub = types.ModuleType("connectors")
connectors_stub.__file__ = str(CONNECTORS_DIR / "__init__.py")
connectors_stub.__path__ = [str(CONNECTORS_DIR)]
sys.modules.setdefault("connectors", connectors_stub)


def _load_connector_module(name: str, relative_path: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, CONNECTORS_DIR / relative_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


stage_base = _load_connector_module(
    "connectors.neo_apsu_stage_b", "neo_apsu_stage_b.py"
)

MODULES = {
    "connectors.operator_api_stage_b": _load_connector_module(
        "connectors.operator_api_stage_b", "operator_api_stage_b.py"
    ),
    "connectors.operator_upload_stage_b": _load_connector_module(
        "connectors.operator_upload_stage_b", "operator_upload_stage_b.py"
    ),
    "connectors.crown_handshake_stage_b": _load_connector_module(
        "connectors.crown_handshake_stage_b", "crown_handshake_stage_b.py"
    ),
}


@pytest.fixture(autouse=True)
def _enable_stage_b(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(stage_base, "_MCP_ENABLED", True)
    monkeypatch.setattr(stage_base, "_MCP_URL", "https://mcp.test")
    monkeypatch.setenv("ABZU_USE_MCP", "1")
    monkeypatch.setenv("MCP_GATEWAY_URL", "https://mcp.test")


@pytest.mark.parametrize(
    "module_name",  # type: ignore[var-annotated]
    [
        "connectors.operator_api_stage_b",
        "connectors.operator_upload_stage_b",
        "connectors.crown_handshake_stage_b",
    ],
)
def test_handshake_payload_contains_expected_identity(
    module_name: str, caplog: pytest.LogCaptureFixture
) -> None:
    module = MODULES[module_name]
    caplog.set_level("INFO", logger=module.LOGGER.name)
    observed: dict[str, Any] = {}

    def _capture(request: httpx.Request) -> httpx.Response:
        nonlocal observed
        observed = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "authenticated": True,
                "session": {
                    "id": "sess-123",
                    "credential_expiry": "2025-10-12T00:00:00Z",
                },
                "accepted_contexts": [stage_base._STAGE_B_CONTEXT],
            },
        )

    async def _run() -> dict[str, Any]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(_capture)) as client:
            return await module.handshake(client=client)

    result = asyncio.run(_run())

    assert (
        observed["identity"]["connector_id"] == module._CONNECTOR._config.connector_id
    )
    assert result["session"]["id"] == "sess-123"
    assert any(
        "Stage B rehearsal handshake acknowledged" in record.getMessage()
        for record in caplog.records
    )
    context = observed["supported_contexts"][0]
    assert stage_base._STAGE_B_CONTEXT == context["name"]
    assert context["channels"]
    assert context["capabilities"]


@pytest.mark.parametrize(
    "module_name, expected_chakra",
    [
        ("connectors.operator_api_stage_b", "operator"),
        ("connectors.operator_upload_stage_b", "operator"),
        ("connectors.crown_handshake_stage_b", "crown"),
    ],
)
def test_send_heartbeat_merges_defaults(module_name: str, expected_chakra: str) -> None:
    module = MODULES[module_name]
    recorded: list[dict[str, Any]] = []

    def _capture(request: httpx.Request) -> httpx.Response:
        recorded.append(json.loads(request.content))
        return httpx.Response(202)

    session_info = {
        "id": "sess-789",
        "credential_expiry": "2025-12-01T00:00:00Z",
    }

    async def _run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(_capture)) as client:
            await module.send_heartbeat(
                {"status": "aligned"},
                client=client,
                session=session_info,
            )

    asyncio.run(_run())

    assert recorded
    payload = recorded[-1]
    assert payload["chakra"] == expected_chakra
    assert payload["cycle_count"] == 0
    assert payload["context"] == stage_base._STAGE_B_CONTEXT
    assert payload["credential_expiry"] == "2025-12-01T00:00:00Z"
    assert payload["status"] == "aligned"


@pytest.mark.parametrize(
    "module_name",
    [
        "connectors.operator_api_stage_b",
        "connectors.operator_upload_stage_b",
        "connectors.crown_handshake_stage_b",
    ],
)
def test_doctrine_compliance_passes(module_name: str) -> None:
    module = MODULES[module_name]
    compliant, failures = module.doctrine_compliant()
    assert compliant, failures
