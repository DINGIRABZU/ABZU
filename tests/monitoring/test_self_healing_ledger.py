from __future__ import annotations

import json
from pathlib import Path

from distributed_memory import HeartbeatTimestampStore
from monitoring.self_healing_ledger import SelfHealingLedger


def test_log_continuity_and_state_recovery(tmp_path: Path) -> None:
    log_file = tmp_path / "self_healing.json"
    store = HeartbeatTimestampStore(path=tmp_path / "beats.json")

    ledger = SelfHealingLedger(store=store, log_path=log_file)
    ledger.component_down("root", timestamp=1)
    ledger.repair_attempt("root", timestamp=2)
    ledger.final_status("root", "recovered", timestamp=3)

    # simulate restart
    ledger = SelfHealingLedger(store=store, log_path=log_file)
    state = ledger.recover_state()
    assert state == {"root": 3}

    ledger.component_down("root", timestamp=4)
    ledger.final_status("root", "recovered", timestamp=5)

    lines = [json.loads(line) for line in log_file.read_text().splitlines()]
    assert len(lines) == 5
    assert lines[0]["event"] == "component_down"
    assert lines[3]["event"] == "component_down"

    state = ledger.recover_state()
    assert state == {"root": 5}
