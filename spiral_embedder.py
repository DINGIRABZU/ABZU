from __future__ import annotations

"""CLI helper for inserting embeddings into ``spiral_vector_db``."""

from pathlib import Path
import argparse
import json


import spiral_vector_db as svdb


def _load(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [dict(d) for d in data]
    except Exception:
        pass
    items: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            items.append(json.loads(line))
        except Exception:
            continue
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
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON or JSONL")
    parser.add_argument("--db-path", help="Database directory")
    args = parser.parse_args(argv)
    count = insert_file(Path(args.in_path), Path(args.db_path) if args.db_path else None)
    print(count)
    return 0


__all__ = ["insert_file", "main"]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

