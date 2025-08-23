from __future__ import annotations

import argparse
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

VECTOR_LOG = Path("data/vector_memory.log")
REGISTRY_DB = Path("data/spiral_registry.db")


def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d%H%M%S")


def snapshot(dest: Path) -> None:
    """Copy current memory files to ``dest`` with a timestamp."""

    dest.mkdir(parents=True, exist_ok=True)
    ts = _timestamp()
    if VECTOR_LOG.exists():
        shutil.copy2(VECTOR_LOG, dest / f"vector_memory_{ts}.log")
    if REGISTRY_DB.exists():
        shutil.copy2(REGISTRY_DB, dest / f"spiral_registry_{ts}.db")


def restore(src: Path) -> None:
    """Restore the most recent backups from ``src``."""

    src.mkdir(parents=True, exist_ok=True)
    logs = sorted(src.glob("vector_memory_*.log"))
    dbs = sorted(src.glob("spiral_registry_*.db"))
    if logs:
        VECTOR_LOG.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(logs[-1], VECTOR_LOG)
    if dbs:
        REGISTRY_DB.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dbs[-1], REGISTRY_DB)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Manage off-site backups")
    sub = parser.add_subparsers(dest="command", required=True)

    snap = sub.add_parser("snapshot", help="Create backups")
    snap.add_argument(
        "--dest",
        type=Path,
        default=Path(os.environ.get("OFFSITE_BACKUP_DIR", "offsite_backups")),
    )
    snap.add_argument(
        "--interval",
        type=int,
        default=0,
        help="Minutes between snapshots; 0 runs once",
    )

    res = sub.add_parser("restore", help="Restore latest backups")
    res.add_argument(
        "--src",
        type=Path,
        default=Path(os.environ.get("OFFSITE_BACKUP_DIR", "offsite_backups")),
    )

    args = parser.parse_args(argv)
    if args.command == "snapshot":
        if args.interval > 0:
            while True:
                snapshot(args.dest)
                time.sleep(args.interval * 60)
        else:
            snapshot(args.dest)
    else:
        restore(args.src)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
