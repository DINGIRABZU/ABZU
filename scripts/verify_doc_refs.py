from __future__ import annotations

"""Ensure docs/INDEX.md lists all documentation files."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
INDEX = DOCS / "INDEX.md"


def iter_docs() -> list[Path]:
    paths: list[Path] = []
    for path in DOCS.rglob("*.md"):
        if path.name == "INDEX.md":
            continue
        if any(part in {"node_modules", "dist", "build"} for part in path.parts):
            continue
        paths.append(path.relative_to(DOCS))
    return paths


def main() -> int:
    index_text = INDEX.read_text(encoding="utf-8")
    missing = [str(p) for p in iter_docs() if str(p) not in index_text]
    if missing:
        print("missing docs in INDEX.md: " + ", ".join(missing), file=sys.stderr)
        return 1
    print("verify_doc_refs: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
