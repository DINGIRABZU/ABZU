"""Arcade flow tests for web operator."""

import json
from typing import Iterable

import pytest
from fastapi.testclient import TestClient

import operator_service.api as api
from operator_service.api import app
from razar import boot_orchestrator, status_dashboard
from scripts import welcome_banner


@pytest.fixture
def client() -> Iterable[TestClient]:
    """Return TestClient for operator service."""
    with TestClient(app) as c:
        yield c


def test_arcade_flow(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Simulate arcade button presses and verify responses and banner."""
    # Ensure cuneiform banner prints correctly
    welcome_banner.print_banner()
    banner_output = capsys.readouterr().out.strip()
    expected_banner = (
        "\U0001202D\U00012129\U00012306 "
        "\U00012120\U0001208A "
        "\U0001213F\U0001213E\U00012100"
    )
    assert banner_output == expected_banner

    # Arcade page loads with greeting modal
    page_resp = client.get("/")
    assert page_resp.status_code == 200
    assert "Arcade Operator" in page_resp.text
    assert "𒀭𒄩𒌆" in page_resp.text

    # Mock backend behaviors
    monkeypatch.setattr(
        boot_orchestrator,
        "start",
        lambda: iter([json.dumps({"ignition": "ok"})]),
        raising=False,
    )
    monkeypatch.setattr(
        status_dashboard,
        "_component_statuses",
        lambda: [{"name": "comp", "status": "up"}],
    )
    monkeypatch.setattr(api, "query_memory", lambda q: {"memory": "ok"})

    # Ignite button
    resp = client.post("/start_ignition")
    assert resp.status_code == 200
    ignition_logs = [json.loads(line) for line in resp.text.strip().splitlines()]
    assert ignition_logs == [{"ignition": "ok"}]

    # Query button
    resp = client.post("/query", json={"query": "hi"})
    assert resp.status_code == 200
    assert resp.json() == {"memory": "ok"}

    # Status button
    resp = client.get("/status")
    assert resp.status_code == 200
    assert resp.json() == {"components": [{"name": "comp", "status": "up"}]}
