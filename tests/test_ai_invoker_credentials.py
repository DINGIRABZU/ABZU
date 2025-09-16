"""Credential validation tests for :mod:`razar.ai_invoker`."""

import json
from pathlib import Path

import pytest

import razar.ai_invoker as ai_invoker


@pytest.fixture(autouse=True)
def clear_agent_cache() -> None:
    """Ensure each test interacts with a clean configuration cache."""

    ai_invoker.invalidate_agent_config_cache()
    yield
    ai_invoker.invalidate_agent_config_cache()


def _write_agent_config(tmp_path: Path, agent_name: str) -> Path:
    config_path = tmp_path / f"{agent_name}_agents.json"
    config_path.write_text(
        json.dumps({"active": agent_name, "agents": [{"name": agent_name}]}),
        encoding="utf-8",
    )
    return config_path


@pytest.mark.parametrize(
    ("agent_name", "env_key"),
    (
        ("kimi2", "KIMI2_API_KEY"),
        ("airstar", "AIRSTAR_API_KEY"),
        ("rstar", "RSTAR_API_KEY"),
    ),
)
def test_required_agent_secret_missing_raises(
    agent_name: str,
    env_key: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Missing dedicated environment variables surface as hard failures."""

    config_path = _write_agent_config(tmp_path, agent_name)
    ai_invoker.invalidate_agent_config_cache(config_path)

    for key in (
        "KIMI2_API_KEY",
        "AIRSTAR_API_KEY",
        "RSTAR_API_KEY",
        "KIMI2_TOKEN",
        "AIRSTAR_TOKEN",
        "RSTAR_TOKEN",
    ):
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(ai_invoker.AgentCredentialError) as exc_info:
        ai_invoker.load_agent_definitions(config_path)

    message = str(exc_info.value)
    assert env_key in message
    assert agent_name.lower() in message.lower()


@pytest.mark.parametrize(
    ("agent_name", "env_key"),
    (
        ("kimi2", "KIMI2_API_KEY"),
        ("airstar", "AIRSTAR_API_KEY"),
        ("rstar", "RSTAR_API_KEY"),
    ),
)
def test_required_agent_secret_rejects_blank_value(
    agent_name: str,
    env_key: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Whitespace-only values are treated as invalid secrets."""

    config_path = _write_agent_config(tmp_path, agent_name)
    ai_invoker.invalidate_agent_config_cache(config_path)

    monkeypatch.setenv(env_key, "   ")

    with pytest.raises(ai_invoker.AgentCredentialError) as exc_info:
        ai_invoker.load_agent_definitions(config_path)

    message = str(exc_info.value)
    assert "must not be empty" in message
    assert env_key in message


def test_required_agent_secret_loaded_from_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Valid environment variables are wired into the agent definitions."""

    config_path = _write_agent_config(tmp_path, "kimi2")
    ai_invoker.invalidate_agent_config_cache(config_path)

    monkeypatch.setenv("KIMI2_API_KEY", "secret-value")

    _active, definitions = ai_invoker.load_agent_definitions(config_path)
    kimi_definition = next(d for d in definitions if d.normalized == "kimi2")
    assert kimi_definition.token == "secret-value"
