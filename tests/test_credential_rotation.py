"""Tests for the remote agent credential rotation helper."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import yaml

from scripts import rotate_remote_agent_keys as rotation
from tests.conftest import allow_test

allow_test(__file__)


def _write_config(path: Path, token: str) -> None:
    payload = {
        "active": "demo_agent",
        "agents": [
            {
                "name": "demo_agent",
                "endpoint": "https://example.invalid/api",
                "auth": {"token": token},
            }
        ],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _read_token(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["agents"][0]["auth"]["token"]


def test_rotation_placeholder_refreshes_cache(monkeypatch, tmp_path):
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir()
    config_path = tmp_path / "config.json"
    _write_config(config_path, token="OLD_DEMO_TOKEN")

    metadata = {
        "agents": [
            {
                "name": "demo_agent",
                "env": "DEMO_AGENT_TOKEN",
                "config_path": str(config_path),
            }
        ]
    }
    (secrets_dir / "rotation.yaml").write_text(
        yaml.safe_dump(metadata), encoding="utf-8"
    )

    rotation.ai_invoker.invalidate_agent_config_cache()

    monkeypatch.setenv("DEMO_AGENT_TOKEN", "OLD_DEMO_TOKEN")
    calls: list[Path | None] = []
    original_invalidate = rotation.ai_invoker.invalidate_agent_config_cache

    def record(path: Path | str | None = None) -> None:
        calls.append(None if path is None else Path(path).resolve())
        original_invalidate(path)

    monkeypatch.setattr(rotation.ai_invoker, "invalidate_agent_config_cache", record)

    results = rotation.rotate_remote_agent_keys(
        secrets_dir=secrets_dir,
        dry_run=False,
    )

    assert len(results) == 1
    [result] = results
    placeholder = result.placeholder
    assert placeholder.startswith("ROTATE_")
    assert placeholder != "OLD_DEMO_TOKEN"
    assert _read_token(config_path) == placeholder
    assert any(call == config_path.resolve() for call in calls if call is not None)
    assert os.environ["DEMO_AGENT_TOKEN"] == "OLD_DEMO_TOKEN"

    monkeypatch.setenv("DEMO_AGENT_TOKEN", placeholder)
    rotation.ai_invoker.invalidate_agent_config_cache(config_path)
    _active, definitions = rotation.ai_invoker.load_agent_definitions(config_path)
    demo_entry = next(item for item in definitions if item.normalized == "demo_agent")
    assert demo_entry.token == placeholder


def test_rotate_remote_agent_keys_missing_agent_raises(tmp_path):
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir()
    config_path = tmp_path / "config.json"
    _write_config(config_path, token="UNCHANGED")

    metadata = {
        "agents": [
            {
                "name": "ghost_agent",
                "config_path": str(config_path),
            }
        ]
    }
    (secrets_dir / "rotation.json").write_text(json.dumps(metadata), encoding="utf-8")

    rotation.ai_invoker.invalidate_agent_config_cache()

    with pytest.raises(rotation.RotationError) as exc:
        rotation.rotate_remote_agent_keys(secrets_dir=secrets_dir, dry_run=False)
    assert "ghost_agent" in str(exc.value)
    assert _read_token(config_path) == "UNCHANGED"


def test_rotate_remote_agent_keys_detects_placeholder_collision(tmp_path):
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir()
    config_path = tmp_path / "config.json"
    existing_placeholder = "ROTATE_DEMO_AGENT_TOKEN_TOKEN"
    _write_config(config_path, token=existing_placeholder)

    metadata = {
        "agents": [
            {
                "name": "demo_agent",
                "env": "DEMO_AGENT_TOKEN",
                "config_path": str(config_path),
            }
        ]
    }
    (secrets_dir / "rotation.yaml").write_text(
        yaml.safe_dump(metadata), encoding="utf-8"
    )

    rotation.ai_invoker.invalidate_agent_config_cache()

    with pytest.raises(rotation.RotationError) as exc:
        rotation.rotate_remote_agent_keys(secrets_dir=secrets_dir, dry_run=False)
    assert "matches existing credential" in str(exc.value)
    assert _read_token(config_path) == existing_placeholder
