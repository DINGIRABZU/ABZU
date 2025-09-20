"""Tests for the Neo-APSU connector template handshake."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import asyncio
import httpx
import pytest

from tests.conftest import ALLOWED_TESTS, allow_test

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "connectors"
    / "neo_apsu_connector_template.py"
)
spec = importlib.util.spec_from_file_location(
    "tests.connectors.neo_apsu_connector_template", MODULE_PATH
)
assert spec and spec.loader
connector = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = connector
spec.loader.exec_module(connector)

allow_test(__file__)
assert str(Path(__file__).resolve()) in ALLOWED_TESTS


def _stub_gateway(responses: list[httpx.Response]) -> httpx.MockTransport:
    """Return a transport that replays ``responses`` sequentially."""

    calls = 0

    def _handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        assert request.method == "POST"
        assert request.url.path.endswith("/handshake")
        calls += 1
        try:
            return responses[calls - 1]
        except IndexError:  # pragma: no cover - defensive
            raise AssertionError("unexpected extra handshake call")

    return httpx.MockTransport(_handler)


@pytest.fixture(autouse=True)
def _enable_mcp(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure the template treats MCP as enabled during tests."""

    monkeypatch.setattr(connector, "_USE_MCP", True)
    monkeypatch.setattr(connector, "_MCP_URL", "https://mcp.test")


def test_handshake_posts_payload_and_logs(caplog: pytest.LogCaptureFixture) -> None:
    """Handshake sends the capability payload and logs Stage B acknowledgement."""

    caplog.set_level("INFO", logger=connector.__name__)

    observed_payload: dict[str, object] = {}

    def _capture_payload(request: httpx.Request) -> httpx.Response:
        nonlocal observed_payload
        observed_payload = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "authenticated": True,
                "session": {"id": "sess-123", "expires_at": "2025-10-12T00:00:00Z"},
                "accepted_contexts": ["stage-b-rehearsal"],
            },
        )

    async def _run() -> dict[str, object]:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(_capture_payload)
        ) as client:
            return await connector.handshake(client=client)

    response = asyncio.run(_run())

    assert response["session"]["id"] == "sess-123"
    assert observed_payload["identity"] == {
        "connector_id": "neo_apsu_connector_template",
        "version": connector.__version__,
        "instance": "local",
    }
    assert observed_payload["supported_contexts"][0]["name"] == "stage-b-rehearsal"
    assert observed_payload["rotation"]["supports_hot_swap"] is True

    log_messages = [record.getMessage() for record in caplog.records]
    assert "Stage B rehearsal handshake acknowledged" in log_messages


def test_handshake_retries_until_authenticated(monkeypatch: pytest.MonkeyPatch) -> None:
    """Gateway responses marked unauthenticated trigger retries before succeeding."""

    responses = [
        httpx.Response(200, json={"authenticated": False, "accepted_contexts": []}),
        httpx.Response(
            200,
            json={
                "authenticated": True,
                "session": {"id": "sess-456"},
                "accepted_contexts": [
                    {"name": "stage-b-rehearsal", "status": "accepted"}
                ],
            },
        ),
    ]

    transport = _stub_gateway(responses)
    sleeps: list[float] = []

    async def _fake_sleep(duration: float) -> None:
        sleeps.append(duration)

    monkeypatch.setattr(connector.asyncio, "sleep", _fake_sleep)

    async def _run() -> dict[str, object]:
        async with httpx.AsyncClient(transport=transport) as client:
            return await connector.handshake(client=client, retries=3)

    result = asyncio.run(_run())

    assert result["session"]["id"] == "sess-456"
    assert sleeps  # backoff executed at least once


def test_handshake_raises_after_exhausting_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Failure to obtain authentication raises an error after retries are exhausted."""

    responses = [
        httpx.Response(200, json={"authenticated": False, "accepted_contexts": []}),
        httpx.Response(200, json={"authenticated": False, "accepted_contexts": []}),
        httpx.Response(200, json={"authenticated": False, "accepted_contexts": []}),
    ]

    transport = _stub_gateway(responses)

    async def _fake_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(connector.asyncio, "sleep", _fake_sleep)

    async def _run() -> None:
        async with httpx.AsyncClient(transport=transport) as client:
            await connector.handshake(client=client, retries=3)

    with pytest.raises(RuntimeError, match="authentication failed"):
        asyncio.run(_run())


def test_send_heartbeat_requires_mcp_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Heartbeat emission is blocked when MCP is disabled."""

    monkeypatch.setattr(connector, "_USE_MCP", False)

    with pytest.raises(RuntimeError, match="MCP is not enabled"):
        asyncio.run(connector.send_heartbeat({"status": "ok"}))


@pytest.mark.asyncio
async def test_send_heartbeat_applies_canonical_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Heartbeat payloads merge canonical defaults and validate overrides."""

    monkeypatch.setattr(connector, "_USE_MCP", True)

    recorded: list[dict[str, object]] = []

    def _capture(request: httpx.Request) -> httpx.Response:
        recorded.append(json.loads(request.content))
        return httpx.Response(202)

    session_info = {"id": "sess-123", "expires_at": "2025-10-12T00:00:00Z"}

    transport = httpx.MockTransport(_capture)

    async with httpx.AsyncClient(transport=transport) as client:
        await connector.send_heartbeat(
            {"status": "aligned"},
            client=client,
            session=session_info,
        )

    assert recorded
    baseline = recorded[-1]
    assert baseline["chakra"] == "neo"
    assert baseline["cycle_count"] == 0
    assert baseline["credential_expiry"] == "2025-10-12T00:00:00Z"


def test_doctrine_compliant_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Doctrine compliance passes when registry, schema, and rotation metadata align."""

    monkeypatch.setenv("MCP_LAST_ROTATED", connector._iso_now())
    monkeypatch.setenv("MCP_ROTATION_WINDOW", "PT24H")

    compliant, reasons = connector.doctrine_compliant()

    assert compliant
    assert reasons == []


def test_doctrine_compliant_reports_failures(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Doctrine compliance reports all failed checks."""

    monkeypatch.setenv("MCP_LAST_ROTATED", "2020-01-01T00:00:00Z")
    monkeypatch.setenv("MCP_ROTATION_WINDOW", "PT1H")

    bad_registry = tmp_path / "component_index.json"
    bad_registry.write_text(json.dumps({"components": []}), encoding="utf-8")
    monkeypatch.setattr(connector, "_COMPONENT_INDEX", bad_registry)

    bad_connector_index = tmp_path / "CONNECTOR_INDEX.md"
    bad_connector_index.write_text(
        (
            "| id | purpose | version | auth | endpoints | linked agents | "
            "status | code | docs | schema |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            "| `neo_apsu_connector_template` | template | 0.1.0 | Bearer | "
            "`POST /handshake` | MCP | experimental | N/A | N/A | "
            "[schema](../../schemas/missing.schema.json) |\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(connector, "_CONNECTOR_INDEX", bad_connector_index)

    compliant, reasons = connector.doctrine_compliant()

    assert not compliant
    assert any("component registry" in message for message in reasons)
    assert any("schema" in message for message in reasons)
    assert any("credential rotation" in message for message in reasons)
