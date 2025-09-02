"""Ensure biosignal samples follow expected schema."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

SCHEMA = ["timestamp", "heart_rate", "skin_temp", "eda"]
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "biosignals"


def csv_paths() -> list[Path]:
    return sorted(DATA_DIR.glob("*.csv"))


@pytest.mark.parametrize("csv_path", csv_paths())
def test_csv_schema(csv_path: Path) -> None:
    """CSV files contain expected columns."""
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == SCHEMA
        for row in reader:
            assert set(row.keys()) == set(SCHEMA)


def test_jsonl_schema() -> None:
    """JSONL file contains expected keys."""
    jsonl_path = DATA_DIR / "sample_biosignals_anonymized.jsonl"
    with jsonl_path.open(encoding="utf-8") as handle:
        for line in handle:
            data = json.loads(line)
            assert set(data.keys()) == set(SCHEMA)
