from __future__ import annotations

import csv
from pathlib import Path
import runpy

import pytest

from memory.narrative_engine import StoryEvent
from src.core import config as core_config

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "biosignals"

__version__ = "0.1.0"


def load_dataset(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def dataset_paths() -> list[Path]:
    return sorted(DATA_DIR.glob("*.csv"))


@pytest.mark.parametrize("csv_path", dataset_paths())
def test_ingest_biosignal_dataset(csv_path: Path) -> None:
    rows = load_dataset(csv_path)
    assert len(rows) == 3
    assert set(rows[0].keys()) == {"timestamp", "heart_rate", "skin_temp", "eda"}


@pytest.mark.parametrize("csv_path", dataset_paths())
def test_dataset_values_are_numeric(csv_path: Path) -> None:
    rows = load_dataset(csv_path)
    for row in rows:
        assert float(row["heart_rate"]) >= 0
        assert float(row["skin_temp"]) >= 0
        assert float(row["eda"]) >= 0


@pytest.mark.parametrize("csv_path", dataset_paths())
def test_transform_biosignals_to_event(csv_path: Path) -> None:
    row = load_dataset(csv_path)[1]
    action = "elevated heart rate" if float(row["heart_rate"]) > 74 else "calm"
    event = StoryEvent(actor="subject", action=action)
    assert isinstance(event, StoryEvent)
    assert event.action == action


def test_ingest_script_executes() -> None:
    script = Path(__file__).resolve().parents[2] / "scripts" / "ingest_biosignals.py"
    runpy.run_path(str(script))


def test_config_loader_reads_settings() -> None:
    cfg = core_config.load_config()
    assert cfg.audio.sample_rate > 0
