import json
from pathlib import Path

from razar import mission_logger


def test_log_and_summary(tmp_path):
    mission_logger.LOG_PATH = tmp_path / "logs" / "razar.log"
    mission_logger.log_event("alpha", "success")
    mission_logger.log_event("beta", "pending")

    assert mission_logger.LOG_PATH.exists()
    data = [json.loads(l) for l in mission_logger.LOG_PATH.read_text().splitlines()]
    assert data[0]["component"] == "alpha"

    summary = mission_logger.summarize()
    assert summary["last_success"] == "alpha"
    assert summary["pending"] == ["beta"]

    mission_logger.log_event("beta", "success")
    summary = mission_logger.summarize()
    assert summary["pending"] == []
