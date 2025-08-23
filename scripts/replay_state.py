from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

try:  # pragma: no cover - optional dependency
    from vector_memory import add_vector, LOG_FILE
except Exception:  # pragma: no cover - optional dependency
    add_vector = None  # type: ignore[assignment]
    LOG_FILE = Path("data/vector_memory.log")  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from spiral_memory import REGISTRY_DB
except Exception:  # pragma: no cover - optional dependency
    REGISTRY_DB = Path("data/spiral_registry.db")  # type: ignore[assignment]


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
                continue
            if entry.get("operation") != "add":
                continue
            text = entry.get("text", "")
            meta = entry.get("metadata", {})
            try:
                add_vector(text, meta)
            except Exception:
                continue


def main(argv: list[str] | None = None) -> None:
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
