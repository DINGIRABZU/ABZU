from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents.victim import security_canary


def test_canary_triggers_snapshot_and_alert(tmp_path):
    snap_called = False

    def fake_snap():
        nonlocal snap_called
        snap_called = True
        return tmp_path / "snap.sqlite"

    messages: list[str] = []

    def fake_alert(msg: str) -> None:
        messages.append(msg)

    handled = security_canary.detect_breach(
        True, snap_func=fake_snap, alert=fake_alert
    )

    assert handled is True
    assert snap_called
    assert messages and "snap.sqlite" in messages[0]
