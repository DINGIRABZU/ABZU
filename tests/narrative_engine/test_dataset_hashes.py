"""Verify biosignal dataset hashes."""

from __future__ import annotations

from pathlib import Path

import pytest

from data.biosignals import DATASET_HASHES, hash_file

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "biosignals"


def dataset_paths() -> list[Path]:
    return [p for p in DATA_DIR.iterdir() if p.is_file() and p.name in DATASET_HASHES]


@pytest.mark.parametrize("path", dataset_paths())
def test_dataset_hashes(path: Path) -> None:
    """Datasets match their recorded SHA256 hashes."""
    assert hash_file(path) == DATASET_HASHES[path.name]
