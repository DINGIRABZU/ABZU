import importlib

from worlds.config_registry import export_config, import_config, reset_registry


def test_registration_and_roundtrip(tmp_path, monkeypatch):
    # start with a clean registry
    reset_registry()

    # Reload memory to trigger layer registration
    import memory

    importlib.reload(memory)

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

    cfg = export_config()

    assert set(cfg["layers"]) == set(memory.LAYERS)
    assert cfg["paths"]["emotional"] == str(emo_path)
    assert cfg["brokers"]["redis"]["channel"] == "chan"

    # verify round-trip
    reset_registry()
    import_config(cfg)
    assert export_config() == cfg
