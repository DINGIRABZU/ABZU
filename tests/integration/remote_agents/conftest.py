from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

_FIXTURE_DIR = Path(__file__).parent


def _load_fixture(name: str) -> Dict[str, Any]:
    path = _FIXTURE_DIR / name
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture
def kimi_k2_fixture() -> Dict[str, Any]:
    """Return the sample completion payload published with MoonshotAI's Kimi-K2."""

    return _load_fixture("kimi_k2_completion.json")


@pytest.fixture
def airstar_fixture(kimi_k2_fixture: Dict[str, Any]) -> Dict[str, Any]:
    """Return a replay payload for AirStar derived from the Kimi-K2 sample."""

    payload = json.loads(json.dumps(kimi_k2_fixture))
    payload["request"].setdefault(
        "context",
        {
            "component": "crown_router",
            "error": "Health check failed",
            "attempt": 1,
        },
    )
    payload["request"].setdefault("auth_token", "fixture-token")
    return payload


@pytest.fixture
def rstar_fixture() -> Dict[str, Any]:
    """Return the request/response example from Microsoft's rStar repository."""

    return _load_fixture("rstar_completion.json")
