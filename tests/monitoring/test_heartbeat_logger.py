from __future__ import annotations

import json
from pathlib import Path

from distributed_memory import CycleCounterStore
from monitoring.heartbeat_logger import HeartbeatLogger
from scripts.snapshot_state import create_snapshot, restore_snapshot


def test_log_persistence(tmp_path: Path) -> None:
    log_file = tmp_path / "heartbeat.log"
    store = CycleCounterStore(path=tmp_path / "cycles.json")
    logger = HeartbeatLogger(store=store, log_path=log_file)
    logger.log("root")
    # simulate restart
    logger = HeartbeatLogger(store=store, log_path=log_file)
    logger.log("root")
    lines = [json.loads(l) for l in log_file.read_text().splitlines()]
    assert [entry["cycle_id"] for entry in lines] == [1, 2]


def test_snapshot_restore(tmp_path: Path) -> None:
    registry = tmp_path / "agent_registry.json"
    registry.write_text(json.dumps({"agent": "test"}))
    doctrine = tmp_path / "doctrine_index.md"
    doctrine.write_text("| File | Version |\n| --- | --- |\n| doc.md | 1.0 |\n")
    snap_dir = tmp_path / "snaps"
    snap_path = create_snapshot(
        snap_dir,
        registry_file=registry,
        doctrine_index=doctrine,
    )
    # mutate files to ensure restoration occurs
    registry.write_text("{}")
    restore_snapshot(
        snap_path,
        registry_file=registry,
        doctrine_versions_file=tmp_path / "doctrine_versions.json",
    )
    restored = json.loads(registry.read_text())
    assert restored == {"agent": "test"}
    assert (tmp_path / "doctrine_versions.json").exists()
