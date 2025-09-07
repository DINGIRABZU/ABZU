"""Tests for chakra cycle persistence."""

from __future__ import annotations

__version__ = "0.1.0"

import time

from distributed_memory import CycleCounterStore
from spiral_os.chakra_cycle import ChakraCycle, GEAR_RATIOS


def test_cycle_continuity_after_restart(tmp_path):
    path = tmp_path / "cycles.json"
    store = CycleCounterStore(path=path)
    cycle = ChakraCycle(store=store)
    events = cycle.emit_heartbeat()
    root_event = next(e for e in events if e.chakra == "root")
    assert root_event.cycle_count == GEAR_RATIOS["root"]
    assert root_event.timestamp <= time.time()

    # Restart with same store
    new_cycle = ChakraCycle(store=CycleCounterStore(path=path))
    assert new_cycle.get_cycle("root") == root_event.cycle_count
    new_cycle.emit_heartbeat()
    assert new_cycle.get_cycle("root") == root_event.cycle_count + GEAR_RATIOS["root"]
