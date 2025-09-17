from __future__ import annotations

import copy
import json
from typing import Any, Dict

import pytest

from agents.razar import ai_invoker


class DummyResponse:
    def __init__(self, payload: Dict[str, Any], status_code: int = 200):
        self._payload = copy.deepcopy(payload)
        self.status_code = status_code
        self.text = json.dumps(self._payload)

    def json(self) -> Dict[str, Any]:
        return copy.deepcopy(self._payload)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


@pytest.fixture
def capture_requests(monkeypatch: pytest.MonkeyPatch) -> Dict[str, Any]:
    captured: Dict[str, Any] = {}

    def fake_post(
        url: str,
        *,
        json: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
        timeout: float | None = None,
    ):
        captured["url"] = url
        captured["json"] = copy.deepcopy(json)
        captured["headers"] = dict(headers or {})
        captured["timeout"] = timeout
        payload = captured.get("response_payload")
        return DummyResponse(payload or {"ok": True})

    monkeypatch.setattr(ai_invoker.requests, "post", fake_post)
    return captured


def test_invoke_kimi2_replays_documented_payload(
    kimi_k2_fixture: Dict[str, Any], capture_requests: Dict[str, Any]
) -> None:
    capture_requests["response_payload"] = kimi_k2_fixture["response"]
    request_payload = copy.deepcopy(kimi_k2_fixture["request"])

    module, agent_config, suggestion = ai_invoker._invoke_kimi2(
        "Kimi2",
        "https://kimi.example/v1/completions",
        request_payload,
        "test-kimi-token",
    )

    expected_payload = copy.deepcopy(kimi_k2_fixture["request"])
    expected_payload.setdefault("auth_token", "test-kimi-token")

    assert capture_requests["url"] == "https://kimi.example/v1/completions"
    assert capture_requests["json"] == expected_payload
    assert capture_requests["headers"] == {
        "Authorization": "Bearer test-kimi-token",
        "X-API-Key": "test-kimi-token",
    }
    assert pytest.approx(60.0) == capture_requests["timeout"]

    assert module.__name__ == "Kimi2"
    assert agent_config == {
        "endpoint": "https://kimi.example/v1/completions",
        "service": "kimi2",
        "status_code": 200,
        "token_provided": True,
    }
    assert suggestion == kimi_k2_fixture["response"]
    assert "auth_token" not in request_payload


def test_invoke_airstar_preserves_context_token(
    airstar_fixture: Dict[str, Any], capture_requests: Dict[str, Any]
) -> None:
    capture_requests["response_payload"] = airstar_fixture["response"]
    request_payload = copy.deepcopy(airstar_fixture["request"])

    module, agent_config, suggestion = ai_invoker._invoke_airstar(
        "AirStar",
        "https://airstar.example/v1/completions",
        request_payload,
        "remote-airstar-token",
    )

    expected_payload = copy.deepcopy(airstar_fixture["request"])
    # the auth token already exists in the fixture and should not be replaced
    assert expected_payload["auth_token"] == "fixture-token"

    assert capture_requests["url"] == "https://airstar.example/v1/completions"
    assert capture_requests["json"] == expected_payload
    assert capture_requests["headers"] == {
        "Authorization": "Bearer remote-airstar-token",
        "X-API-Key": "remote-airstar-token",
    }
    assert pytest.approx(60.0) == capture_requests["timeout"]

    assert module.__name__ == "AirStar"
    assert agent_config == {
        "endpoint": "https://airstar.example/v1/completions",
        "service": "airstar",
        "status_code": 200,
        "token_provided": True,
    }
    assert suggestion == airstar_fixture["response"]
    assert request_payload["auth_token"] == "fixture-token"


def test_invoke_rstar_replays_reference_payload(
    rstar_fixture: Dict[str, Any], capture_requests: Dict[str, Any]
) -> None:
    capture_requests["response_payload"] = rstar_fixture["response"]
    request_payload = copy.deepcopy(rstar_fixture["request"])

    module, agent_config, suggestion = ai_invoker._invoke_rstar(
        "RStar", "https://rstar.example/v1/completions", request_payload, "rstar-secret"
    )

    expected_payload = copy.deepcopy(rstar_fixture["request"])
    expected_payload.setdefault("auth_token", "rstar-secret")

    assert capture_requests["url"] == "https://rstar.example/v1/completions"
    assert capture_requests["json"] == expected_payload
    assert capture_requests["headers"] == {
        "Authorization": "Bearer rstar-secret",
        "X-API-Key": "rstar-secret",
    }
    assert pytest.approx(60.0) == capture_requests["timeout"]

    assert module.__name__ == "RStar"
    assert agent_config == {
        "endpoint": "https://rstar.example/v1/completions",
        "service": "rstar",
        "status_code": 200,
        "token_provided": True,
    }
    assert suggestion == rstar_fixture["response"]
    assert "auth_token" not in request_payload
