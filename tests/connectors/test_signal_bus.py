from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]


def _load_signal_bus(monkeypatch, *, redis: bool = False, kafka: bool = False):
    sys.modules.pop("connectors.signal_bus", None)
    if redis:
        monkeypatch.setenv("SIGNAL_BUS_REDIS_URL", "redis://localhost")
        fake_redis = SimpleNamespace(from_url=lambda url: SimpleNamespace())
        monkeypatch.setitem(sys.modules, "redis", fake_redis)
    if kafka:
        monkeypatch.setenv("SIGNAL_BUS_KAFKA_BROKERS", "localhost:9092")

        class _Producer:
            def __init__(self, *a, **k):
                pass

            def send(self, *a, **k):
                pass

            def flush(self):
                pass

        class _Consumer:
            def __init__(self, *a, **k):
                pass

            def __iter__(self):
                return iter(())

            def close(self):
                pass

        fake_kafka = SimpleNamespace(KafkaProducer=_Producer, KafkaConsumer=_Consumer)
        monkeypatch.setitem(sys.modules, "kafka", fake_kafka)
    spec = importlib.util.spec_from_file_location(
        "connectors.signal_bus", ROOT / "connectors" / "signal_bus.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("connectors", ModuleType("connectors"))
    spec.loader.exec_module(module)
    return module


def test_inmemory_publish_subscribe(monkeypatch) -> None:
    bus = _load_signal_bus(monkeypatch)
    received: list[dict] = []
    bus.subscribe("root", received.append)
    bus.publish("root", {"msg": "hi"})
    assert received == [{"msg": "hi", "chakra": "root"}]


def test_selects_redis(monkeypatch) -> None:
    bus = _load_signal_bus(monkeypatch, redis=True)
    assert type(bus._bus).__name__ == "_RedisBus"


def test_selects_kafka(monkeypatch) -> None:
    bus = _load_signal_bus(monkeypatch, kafka=True)
    assert type(bus._bus).__name__ == "_KafkaBus"
