import json
from datetime import datetime
from pathlib import Path

from agents.razar import mission_logger


def test_log_format_and_fields(tmp_path: Path, monkeypatch) -> None:
    """Mission logger writes structured lifecycle events."""

    log_file = tmp_path / "razar.log"
    monkeypatch.setattr(mission_logger, "LOG_PATH", log_file)

    mission_logger.log_start("alpha", "success", "booted")
    mission_logger.log_error("beta", "failure")
    mission_logger.log_resolved("beta", "restored", "patched")
    mission_logger.log_event(mission_logger.Lifecycle.SHUTDOWN, "alpha", "ok")

    entries = [json.loads(line) for line in log_file.read_text().splitlines()]

    assert entries[0]["event"] == "start"
    assert entries[0]["details"] == "booted"
    assert "details" not in entries[1]

    required = {"event", "component", "status", "timestamp"}
    for entry in entries:
        assert required <= entry.keys()
        # ISO-8601 parse check raises ValueError on invalid format
        datetime.fromisoformat(entry["timestamp"])

    assert any(e["event"] == "resolved" for e in entries)
    assert any(e["event"] == "shutdown" for e in entries)
