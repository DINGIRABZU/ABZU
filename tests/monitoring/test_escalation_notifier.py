from __future__ import annotations

from datetime import datetime
from pathlib import Path

import json
import pytest

from monitoring import escalation_notifier


def _make_logs(tmp_path: Path, razar: str = "", crown: str = "") -> tuple[Path, Path]:
    r_path = tmp_path / "razar.log"
    c_path = tmp_path / "crown.log"
    r_path.write_text(razar)
    c_path.write_text(crown)
    return r_path, c_path


def test_repeated_requests_trigger_escalation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    razar_lines = """
2025-01-01T00:00:00Z db request
2025-01-01T00:05:00Z db request
2025-01-01T00:09:00Z db request
""".strip()
    r_log, c_log = _make_logs(tmp_path, razar=razar_lines)

    events: list[dict[str, object]] = []

    async def fake_broadcast(
        event: dict[str, object]
    ) -> None:  # pragma: no cover - patch
        events.append(event)

    monkeypatch.setattr(escalation_notifier, "broadcast_event", fake_broadcast)
    monkeypatch.setattr(
        escalation_notifier, "ESCALATION_LOG", tmp_path / "operator_escalations.jsonl"
    )

    now = datetime.fromisoformat("2025-01-01T00:10:00")
    result = escalation_notifier.scan_logs(r_log, c_log, now=now)

    assert result and result[0]["component"] == "db"
    stored = json.loads(
        (tmp_path / "operator_escalations.jsonl").read_text().splitlines()[0]
    )
    assert stored["reason"] == "repeated_requests"
    assert events[0]["component"] == "db"


def test_service_offline_triggers_escalation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    crown_lines = "2025-01-01T00:00:00Z api offline"
    r_log, c_log = _make_logs(tmp_path, crown=crown_lines)

    events: list[dict[str, object]] = []

    async def fake_broadcast(
        event: dict[str, object]
    ) -> None:  # pragma: no cover - patch
        events.append(event)

    monkeypatch.setattr(escalation_notifier, "broadcast_event", fake_broadcast)
    monkeypatch.setattr(
        escalation_notifier, "ESCALATION_LOG", tmp_path / "operator_escalations.jsonl"
    )

    now = datetime.fromisoformat("2025-01-01T00:06:00")
    result = escalation_notifier.scan_logs(r_log, c_log, now=now)

    assert result and result[0]["component"] == "api"
    stored = json.loads(
        (tmp_path / "operator_escalations.jsonl").read_text().splitlines()[0]
    )
    assert stored["reason"] == "service_offline"
    assert events[0]["reason"] == "service_offline"
