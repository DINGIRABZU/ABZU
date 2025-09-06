"""Reindex ethics corpus files into the Chroma vector store."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directory",
        type=Path,
        nargs="?",
        default=Path("sacred_inputs"),
        help="Folder containing ethics markdown files",
    )
    return parser.parse_args()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    args = _parse_args()
    if not ingest_ethics(args.directory):
        raise SystemExit(1)
