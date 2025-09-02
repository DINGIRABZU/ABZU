"""Tests for mission logger."""

import json
from razar import mission_logger


def test_log_and_timeline(tmp_path):
    mission_logger.LOG_PATH = tmp_path / "logs" / "razar.log"
    mission_logger.log_start("alpha", "success")
    mission_logger.log_health("beta", "fail")
    mission_logger.log_quarantine("beta", "isolated")
    mission_logger.log_patch("beta", "restart")

    assert mission_logger.LOG_PATH.exists()
    data = [json.loads(l) for l in mission_logger.LOG_PATH.read_text().splitlines()]
    assert data[0]["event"] == "start"

    timeline = mission_logger.timeline()
    assert [e["event"] for e in timeline] == ["start", "health", "quarantine", "patch"]

    summary = mission_logger.summarize(event_filter="start")
    assert summary["last_success"] == "alpha"
    assert summary["pending"] == []

    mission_logger.log_start("gamma", "pending")
    summary = mission_logger.summarize(event_filter="start")
    assert summary["pending"] == ["gamma"]
