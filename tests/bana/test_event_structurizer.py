import csv
from pathlib import Path

import jsonschema
import pytest

from bana import event_structurizer as es

__version__ = "0.0.0"

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "biosignals"


def test_from_interaction_valid() -> None:
    event = es.from_interaction(
        "agent", "ping", {"val": 1}, timestamp="2020-01-01T00:00:00Z"
    )
    assert event["agent_id"] == "agent"
    assert event["event_type"] == "ping"
    assert event["payload"] == {"val": 1}
    es._validate(event)


def test_from_biosignal_row_dataset() -> None:
    csv_path = DATA_DIR / "sample_biosignals_theta.csv"
    row = next(csv.DictReader(csv_path.open()))
    event = es.from_biosignal_row(row, agent_id="sensor", event_type="biosignal")
    assert event["payload"]["heart_rate"] == "72"


def test_validate_missing_field() -> None:
    bad = {"time": "now"}
    with pytest.raises(jsonschema.ValidationError):
        es._validate(bad)
