"""Reindex ethics corpus files into the Chroma vector store."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import mkdtemp

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from INANNA_AI import corpus_memory

__version__ = "0.1.0"

logger = logging.getLogger(__name__)


def ingest_ethics(directory: Path) -> bool:
    """Reindex Markdown files under ``directory`` into Chroma.

    Returns ``True`` on success.
    """
    logger.info("Starting ethics ingestion from %s", directory)
    if not directory.exists():
        logger.error("Directory not found: %s", directory)
        return False
    success = corpus_memory.reindex_corpus([directory])
    if success:
        logger.info("Ethics corpus reindexed from %s", directory)
    else:
        logger.error("Failed to reindex corpus from %s", directory)
    return success


def _stable_timestamp() -> str:
    """Return a UTC timestamp truncated to second precision."""

    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _sha256(path: Path) -> str:
    """Return the SHA256 hex digest for ``path``."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dump_sqlite(db_path: Path, dump_path: Path) -> None:
    """Write a deterministic SQLite dump for ``db_path``."""

    conn = sqlite3.connect(str(db_path))
    try:
        with dump_path.open("w", encoding="utf-8") as handle:
            for line in conn.iterdump():
                handle.write(f"{line}\n")
    finally:
        conn.close()


def _capture_manifest(snapshot_root: Path) -> dict:
    """Generate metadata describing files beneath ``snapshot_root``."""

    entries = []
    for fp in sorted(snapshot_root.rglob("*")):
        if fp.is_file():
            entries.append(
                {
                    "path": str(fp.relative_to(snapshot_root)),
                    "size": fp.stat().st_size,
                    "sha256": _sha256(fp),
                }
            )
    return {
        "generated_at": _stable_timestamp(),
        "files": entries,
    }


def build_chroma_seed_snapshot(
    directory: Path | None = None,
    *,
    output_dir: Path | None = None,
) -> Path:
    """Reindex the ethics corpus and capture a reproducible seed snapshot.

    Parameters
    ----------
    directory:
        Source directory containing Markdown ethics documents. Defaults to
        ``sacred_inputs`` relative to the repository root.
    output_dir:
        Optional destination directory for the snapshot artefacts. When not
        provided a unique temporary directory is created and returned.

    Returns
    -------
    Path
        Path to the directory containing the copied Chroma payload, manifest
        and SQLite dump.

    Raises
    ------
    RuntimeError
        If the ingestion step fails.
    FileNotFoundError
        If the Chroma directory was not produced.
    """

    directory = directory or Path("sacred_inputs")
    if not ingest_ethics(directory):
        raise RuntimeError(f"Failed to ingest ethics corpus from {directory}")

    from INANNA_AI.corpus_memory import CHROMA_DIR

    if not CHROMA_DIR.exists():
        raise FileNotFoundError(f"Chroma directory not found at {CHROMA_DIR}")

    if output_dir is None:
        output_dir = Path(mkdtemp(prefix="chroma_seed_"))
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    snapshot_dir = output_dir / "chroma"
    if snapshot_dir.exists():
        shutil.rmtree(snapshot_dir)
    shutil.copytree(CHROMA_DIR, snapshot_dir)

    manifest = _capture_manifest(snapshot_dir)
    manifest["source_directory"] = str(directory.resolve())
    manifest["chroma_subdir"] = str(snapshot_dir.relative_to(output_dir))

    manifest_path = output_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")

    sqlite_path = snapshot_dir / "chroma.sqlite3"
    dump_path = output_dir / "chroma.dump.sql"
    if sqlite_path.exists():
        _dump_sqlite(sqlite_path, dump_path)
    else:
        dump_path.write_text("-- chroma.sqlite3 not present\n", encoding="utf-8")

    logger.info("Chroma seed snapshot captured at %s", output_dir)
    return output_dir


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directory",
        type=Path,
        nargs="?",
        default=Path("sacred_inputs"),
        help="Folder containing ethics markdown files",
    )
    parser.add_argument(
        "--emit-seed",
        action="store_true",
        help="Capture a Chroma snapshot manifest after ingestion",
    )
    parser.add_argument(
        "--seed-output",
        type=Path,
        help="Optional directory to store the generated Chroma seed",
    )
    return parser.parse_args()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    args = _parse_args()
    if args.emit_seed:
        try:
            snapshot_dir = build_chroma_seed_snapshot(
                args.directory, output_dir=args.seed_output
            )
        except Exception as exc:  # pragma: no cover - CLI feedback path
            logger.error("Failed to capture Chroma seed snapshot", exc_info=True)
            raise SystemExit(1) from exc
        payload = {
            "snapshot_dir": str(snapshot_dir),
            "manifest": str(snapshot_dir / "manifest.json"),
            "sqlite_dump": str(snapshot_dir / "chroma.dump.sql"),
        }
        print(json.dumps(payload))
    else:
        if not ingest_ethics(args.directory):
            raise SystemExit(1)
