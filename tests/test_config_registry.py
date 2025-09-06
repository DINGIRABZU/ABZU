import importlib
from pathlib import Path

import pytest

from worlds.config_registry import (
    export_config,
    export_config_file,
    import_config,
    import_config_file,
    reset_registry,
    register_remote_attempt,
    register_patch,
)


def test_registration_and_roundtrip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # start with a clean registry
    reset_registry()

    # Reload memory to trigger layer registration
    import memory
    import agents

    importlib.reload(memory)
    importlib.reload(agents)

    # Register a path via emotional layer initialiser
    from memory.emotional import get_connection

    emo_path = tmp_path / "emotions.db"
    get_connection(emo_path)

    # Register a broker via event bus
    import agents.event_bus as eb

    eb.set_event_producer(None)
    monkeypatch.setenv("CITADEL_REDIS_CHANNEL", "chan")
    monkeypatch.setenv("CITADEL_REDIS_URL", "redis://localhost")
    eb._get_producer()

    # Register remote repair metadata
    register_remote_attempt("demo")
    register_patch("demo", "patch1", "abc123")

    cfg = export_config()

    assert set(cfg["layers"]) == set(memory.LAYERS)
    assert set(cfg["agents"]) == set(agents.AGENTS)
    assert cfg["paths"]["emotional"] == str(emo_path)
    assert cfg["brokers"]["redis"]["channel"] == "chan"
    assert cfg["remote_attempts"]["demo"] == 1
    assert cfg["component_hashes"]["demo"] == "abc123"
    assert cfg["patches"] == [
        {"component": "demo", "patch": "patch1", "hash": "abc123"}
    ]

    # verify round-trip via dictionary
    reset_registry()
    import_config(cfg)
    assert export_config() == cfg

    # verify file round-trip
    path = tmp_path / "world.json"
    export_config_file(path)
    reset_registry()
    import_config_file(path)
    assert export_config() == cfg
