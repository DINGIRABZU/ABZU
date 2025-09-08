from __future__ import annotations

import json
from pathlib import Path

import pytest

from distributed_memory import CycleCounterStore
from monitoring.heartbeat_logger import HeartbeatLogger
from scripts.snapshot_state import create_snapshot, restore_snapshot


def test_log_survival(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    store = CycleCounterStore(path=tmp_path / "cycles.json")
    logger = HeartbeatLogger(store=store)
    logger.log("root")
    # simulate restart
    logger = HeartbeatLogger(store=store)
    logger.log("root")
    log_file = Path("logs/heartbeat.log")
    lines = [json.loads(line) for line in log_file.read_text().splitlines()]
    assert [entry["cycle_id"] for entry in lines] == [1, 2]


def test_snapshot_restore(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    registry = Path("agents/nazarick/agent_registry.json")
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(json.dumps({"agent": "test"}))
    doctrine = Path("docs/doctrine_index.md")
    doctrine.parent.mkdir(parents=True, exist_ok=True)
    doctrine.write_text("| File | Version |\n| --- | --- |\n| doc.md | 1.0 |\n")
    snap_path = create_snapshot(
        registry_file=registry,
        doctrine_index=doctrine,
    )
    assert snap_path.parent == Path("storage/snapshots")
    # mutate files to ensure restoration occurs
    registry.write_text("{}")
    restore_snapshot(
        snap_path,
        registry_file=registry,
        doctrine_versions_file=Path("doctrine_versions.json"),
    )
    restored = json.loads(registry.read_text())
    assert restored == {"agent": "test"}
    assert Path("doctrine_versions.json").exists()
