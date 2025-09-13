from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
LOGS_DIR = ROOT / "logs"


def boot_sequence() -> dict[str, str]:
    """Initialize minimal services and required paths.

    Ensures data and log directories exist before tests run.
    Returns a mapping with the resolved paths so callers can
    verify initialization if needed.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    return {"data_dir": str(DATA_DIR), "logs_dir": str(LOGS_DIR)}
