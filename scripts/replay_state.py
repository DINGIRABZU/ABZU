"""Restore backups and rebuild vector memory from log files."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import logging
from pathlib import Path

try:  # pragma: no cover - optional dependency
    from vector_memory import LOG_FILE, add_vector
except Exception:  # pragma: no cover - optional dependency
    add_vector = None  # type: ignore[assignment]
    LOG_FILE = Path("data/vector_memory.log")  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from spiral_memory import REGISTRY_DB
except Exception:  # pragma: no cover - optional dependency
    REGISTRY_DB = Path("data/spiral_registry.db")  # type: ignore[assignment]

QUARANTINE_DIR = Path("quarantine")
CORRUPT_LOG = QUARANTINE_DIR / "vector_memory_corrupt.log"
FAILED_LOG = QUARANTINE_DIR / "vector_memory_failed.jsonl"

logger = logging.getLogger(__name__)


def _repair_line(line: str) -> str | None:
    """Try to fix common JSON line issues and return repaired line."""
    candidate = line.strip()
    if candidate.count("{") > candidate.count("}"):
        candidate += "}" * (candidate.count("{") - candidate.count("}"))
    try:
        json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return candidate


def _quarantine(text: str, path: Path) -> None:
    """Append ``text`` to ``path`` within the quarantine directory."""
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"{text}\n")


def replay(src: Path) -> None:
    """Restore latest backups from ``src`` and rebuild vector memory."""
    src.mkdir(parents=True, exist_ok=True)
    log_files = sorted(src.glob("vector_memory_*.log"))
    db_files = sorted(src.glob("spiral_registry_*.db"))
    if log_files:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(log_files[-1], LOG_FILE)
    if db_files:
        REGISTRY_DB.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db_files[-1], REGISTRY_DB)
    if add_vector is None or not LOG_FILE.exists():
        return
    with LOG_FILE.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                repaired = _repair_line(line)
                if repaired is None:
                    logger.warning("Quarantining corrupt log line")
                    _quarantine(line.strip(), CORRUPT_LOG)
                    continue
                entry = json.loads(repaired)
            if entry.get("operation") != "add":
                continue
            text = entry.get("text", "")
            meta = entry.get("metadata", {})
            try:
                add_vector(text, meta)
            except Exception as exc:
                logger.error("Replay failed: %s", exc)
                _quarantine(json.dumps(entry), FAILED_LOG)
                continue


def main(argv: list[str] | None = None) -> None:
    """Parse CLI arguments and replay state from backups."""
    parser = argparse.ArgumentParser(
        description="Replay state from off-site backups",
    )
    parser.add_argument(
        "--src",
        type=Path,
        default=Path(os.environ.get("OFFSITE_BACKUP_DIR", "offsite_backups")),
    )
    args = parser.parse_args(argv)
    replay(args.src)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
