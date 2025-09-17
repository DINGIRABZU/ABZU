import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from scripts import ingest_razar_telemetry as ingest
from tests.conftest import allow_test


allow_test(__file__)


def _write_lines(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines), encoding="utf-8")


def test_ingest_skips_malformed_entries(tmp_path: Path) -> None:
    log_path = tmp_path / "razar_ai_invocations.json"
    base_time = datetime(2024, 5, 1, 12, tzinfo=UTC)
    valid_success = {
        "component": "crown_router",
        "agent": "orion",
        "attempt": 1,
        "patched": True,
        "status": "success",
        "timestamp": base_time.timestamp(),
        "timestamp_iso": base_time.isoformat().replace("+00:00", "Z"),
    }
    valid_failure = {
        "component": "crown_router",
        "agent": "orion",
        "attempt": 2,
        "patched": False,
        "status": "failure",
        "timestamp": (base_time + timedelta(minutes=5)).timestamp(),
        "timestamp_iso": (base_time + timedelta(minutes=5))
        .isoformat()
        .replace("+00:00", "Z"),
    }
    lines = [
        json.dumps(valid_success),
        "not-json",
        json.dumps({"component": "crown_router", "patched": True}),
        json.dumps(valid_failure),
    ]
    _write_lines(log_path, lines)

    output_dir = tmp_path / "ledger"
    trend = ingest.ingest_razar_telemetry(log_path=log_path, output_dir=output_dir)

    assert len(trend) == 1
    row = trend.iloc[0]
    assert row["agent"] == "orion"
    assert row["attempts"] == 2
    assert row["successes"] == 1
    assert row["failures"] == 1
    assert row["success_rate"] == 0.5

    json_output = json.loads((output_dir / "razar_agent_trends.json").read_text())
    assert json_output[0]["component"] == "crown_router"
    assert Path(output_dir / "razar_agent_trends.parquet").exists()


def test_load_invocations_handles_json_array(tmp_path: Path) -> None:
    log_path = tmp_path / "razar_ai_invocations.json"
    base_time = datetime(2024, 6, 2, 9, tzinfo=UTC)
    payload = [
        {
            "component": "memory_bridge",
            "patched": True,
            "timestamp": base_time.timestamp(),
            "timestamp_iso": base_time.isoformat().replace("+00:00", "Z"),
        }
    ]
    log_path.write_text(json.dumps(payload), encoding="utf-8")

    records = ingest.load_invocations(log_path)
    assert len(records) == 1
    assert records[0].agent == "unknown"

    trend = ingest.aggregate_agent_trends(records)
    assert isinstance(trend, pd.DataFrame)
    assert trend.iloc[0]["successes"] == 1
