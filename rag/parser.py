from __future__ import annotations

"""Utility to parse directories into text chunks for RAG."""

from pathlib import Path
from typing import Dict, List
import argparse


def load_inputs(source_dir: Path) -> List[Dict[str, str]]:
    """Return chunks of text from files under ``source_dir``."""
    exts = {".md", ".txt", ".py", ".ipynb", ".json"}
    items: List[Dict[str, str]] = []
    for path in source_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in exts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel_parts = path.relative_to(source_dir).parts
        archetype = rel_parts[0] if len(rel_parts) > 1 else None
        chunk_size = 2000
        for i in range(0, len(text), chunk_size):
            chunk = text[i : i + chunk_size]
            item: Dict[str, str] = {
                "text": chunk,
                "source_path": str(path),
            }
            if archetype:
                item["archetype"] = archetype
            items.append(item)
    return items


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rag_parser")
    parser.add_argument("--dir", default="sacred_inputs", help="Directory to load")
    args = parser.parse_args(argv)
    chunks = load_inputs(Path(args.dir))
    print(len(chunks))
    return 0


__all__ = ["load_inputs", "main"]


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
