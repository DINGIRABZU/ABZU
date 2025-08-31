"""Validate biosignal action transformation during ingestion."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from memory import narrative_engine
from scripts.ingest_biosignals import ingest_directory, ingest_file

__version__ = "0.1.0"

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "biosignals"


def dataset_paths() -> list[Path]:
    return sorted(DATA_DIR.glob("*.csv"))


@pytest.mark.parametrize("csv_path", dataset_paths())
def test_ingest_file_transforms_actions(
    csv_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    logged: list[str] = []
    monkeypatch.setattr(narrative_engine, "log_story", lambda text: logged.append(text))
    monkeypatch.setattr(
        "scripts.ingest_biosignals.log_story", lambda text: logged.append(text)
    )
    ingest_file(csv_path)
    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    expected = [
        "elevated heart rate" if float(r["heart_rate"]) > 74 else "calm" for r in rows
    ]
    assert logged == expected


def test_ingest_directory_logs_all(monkeypatch: pytest.MonkeyPatch) -> None:
    logged: list[str] = []
    monkeypatch.setattr(narrative_engine, "log_story", lambda text: logged.append(text))
    monkeypatch.setattr(
        "scripts.ingest_biosignals.log_story", lambda text: logged.append(text)
    )
    ingest_directory(DATA_DIR)
    assert len(logged) == 3 * len(dataset_paths())
