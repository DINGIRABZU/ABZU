#!/usr/bin/env python3
"""Fail if files contain TODO or FIXME placeholders."""
from __future__ import annotations

import re
import sys
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"(#|//)\s*(TODO|FIXME)\b")
IGNORED_SUFFIXES = {".md"}


def check_file(path: Path) -> list[int]:
    """Return line numbers containing placeholders in *path*."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, FileNotFoundError):
        return []
    hits: list[int] = []
    for idx, line in enumerate(lines, 1):
        if PLACEHOLDER_RE.search(line):
            hits.append(idx)
    return hits


def main(argv: list[str] | None = None) -> int:
    """Check provided files for TODO/FIXME markers."""
    paths = [Path(p) for p in (argv or sys.argv[1:])]
    failed = False
    for path in paths:
        if path.suffix.lower() in IGNORED_SUFFIXES:
            continue
        matches = check_file(path)
        if matches:
            failed = True
            for line_no in matches:
                print(f"{path}:{line_no}: contains TODO/FIXME marker")
    return 1 if failed else 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
