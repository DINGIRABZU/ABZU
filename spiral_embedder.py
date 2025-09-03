"""CLI helper for inserting embeddings into ``spiral_vector_db``."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import spiral_vector_db as svdb

logger = logging.getLogger(__name__)


def _load(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [dict(d) for d in data]
    except json.JSONDecodeError as exc:
        logger.warning(
            "Failed to parse %s as JSON at line %d column %d (char %d): %s",
            path,
            exc.lineno,
            exc.colno,
            exc.pos,
            exc,
        )
    except Exception as exc:  # pragma: no cover - unexpected
        logger.warning("Failed to parse %s as JSON: %s", path, exc)
    items: list[dict] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError as exc:
            logger.warning(
                "Skipping invalid JSON line %d in %s at column %d (char %d): %s",
                lineno,
                path,
                exc.colno,
                exc.pos,
                exc,
            )
        except Exception as exc:  # pragma: no cover - unexpected
            logger.warning("Skipping invalid JSON line %d in %s: %s", lineno, path, exc)
    return items


def insert_file(path: Path, db_path: Path | None = None) -> int:
    """Insert records from ``path`` into the vector DB."""
    if db_path is not None:
        svdb.init_db(db_path)
    items = _load(path)
    svdb.insert_embeddings(items)
    return len(items)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="spiral_embedder")
    parser.add_argument(
        "--in", dest="in_path", required=True, help="Input JSON or JSONL"
    )
    parser.add_argument("--db-path", help="Database directory")
    args = parser.parse_args(argv)
    count = insert_file(
        Path(args.in_path), Path(args.db_path) if args.db_path else None
    )
    print(count)
    return 0


__all__ = ["insert_file", "main"]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
