import time
from typing import Dict

import pytest

from monitoring import chakra_heartbeat
from spiral_os import chakra_cycle


class DummyMemory:
    def __init__(self) -> None:
        self.data: Dict[str, tuple[list[float], dict[str, float]]] = {}

    def backup(self, id_: str, vector: list[float], metadata: dict[str, float]) -> None:
        self.data[id_] = (vector, metadata)

    def restore(self) -> Dict[str, tuple[list[float], dict[str, float]]]:
        return self.data


def test_cycle_emits_all_chakras() -> None:
    cycle = chakra_cycle.ChakraCycle()
    metrics = cycle.emit()
    assert set(metrics) == set(chakra_cycle.GEAR_RATIOS)
    assert all(0.0 <= v < 1.0 for v in metrics.values())


def test_alignment_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    mem = DummyMemory()
    chakra_heartbeat.ChakraHeartbeat.configure(memory=mem, threshold=0.5)
    events = []

    async def fake_broadcast(event):  # pragma: no cover - patched
        events.append(event)

    monkeypatch.setattr(chakra_heartbeat, "broadcast_event", fake_broadcast)

    metrics = {name: 0.0 for name in chakra_cycle.GEAR_RATIOS}
    now = time.time()
    chakra_heartbeat.ChakraHeartbeat.poll(metrics, timestamp=now)
    assert chakra_heartbeat.ChakraHeartbeat.sync_status()
    assert events and events[0]["event"] == "synchronized"

    # desync one chakra
    mem.backup("root", [], {"timestamp": now - 1.0})
    events.clear()
    assert not chakra_heartbeat.ChakraHeartbeat.sync_status()
    assert events == []
