#!/usr/bin/env python3
"""Fail if a Python file lacks a __version__ attribute."""
from __future__ import annotations

import re
import sys
from pathlib import Path

__version__ = "0.1.0"

VERSION_RE = re.compile(r"^__version__\s*=", re.MULTILINE)


def has_version(path: Path) -> bool:
    """Return True if *path* contains a __version__ declaration."""
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return True
    return bool(VERSION_RE.search(text))


def main(argv: list[str] | None = None) -> int:
    """Check provided files for __version__ declaration."""
    paths = [Path(p) for p in (argv or sys.argv[1:])]
    missing = [p for p in paths if p.suffix == ".py" and not has_version(p)]
    for path in missing:
        print(f"{path}: missing __version__")
    return 1 if missing else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
