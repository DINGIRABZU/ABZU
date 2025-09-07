import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "connectors.signal_bus", ROOT / "connectors" / "signal_bus.py"
)
signal_bus = importlib.util.module_from_spec(spec)
sys.modules.setdefault("connectors", ModuleType("connectors"))
spec.loader.exec_module(signal_bus)
publish = signal_bus.publish
subscribe = signal_bus.subscribe


def test_fanout_and_heartbeat() -> None:
    received_a: list[dict] = []
    received_b: list[dict] = []

    subscribe("root", received_a.append)
    subscribe("root", received_b.append)

    publish("root", {"msg": "hi"})

    assert received_a == [{"msg": "hi", "chakra": "root"}]
    assert received_b == [{"msg": "hi", "chakra": "root"}]

    hb_a: list[dict] = []
    hb_b: list[dict] = []
    subscribe("heartbeat", hb_a.append)
    subscribe("heartbeat", hb_b.append)

    publish("heartbeat", {"source": "a"})
    publish("heartbeat", {"source": "b"})

    assert {"source": "a", "chakra": "heartbeat"} in hb_b
    assert {"source": "b", "chakra": "heartbeat"} in hb_a
