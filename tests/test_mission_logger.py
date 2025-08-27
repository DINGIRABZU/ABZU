import json
from razar import mission_logger


def test_log_and_timeline(tmp_path):
    mission_logger.LOG_PATH = tmp_path / "logs" / "razar.log"
    mission_logger.log_launch("alpha", "success")
    mission_logger.log_health_check("beta", "fail")
    mission_logger.log_quarantine("beta", "isolated")
    mission_logger.log_recovery("beta", "restart")

    assert mission_logger.LOG_PATH.exists()
    data = [json.loads(l) for l in mission_logger.LOG_PATH.read_text().splitlines()]
    assert data[0]["event"] == "launch"

    timeline = mission_logger.timeline()
    assert [e["event"] for e in timeline] == ["launch", "health_check", "quarantine", "recovery"]

    summary = mission_logger.summarize(event_filter="launch")
    assert summary["last_success"] == "alpha"
    assert summary["pending"] == []

    mission_logger.log_launch("gamma", "pending")
    summary = mission_logger.summarize(event_filter="launch")
    assert summary["pending"] == ["gamma"]
