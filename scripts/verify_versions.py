#!/usr/bin/env python3
"""Verify module and connector versions match ``component_index.json``."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterable

__version__ = "0.3.0"

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "component_index.json"


def load_index() -> dict[str, tuple[str, str]]:
    """Return mapping of paths to ``(version, type)`` for relevant components."""
    data = json.loads(INDEX_PATH.read_text())
    mapping: dict[str, tuple[str, str]] = {}
    for comp in data.get("components", []):
        comp_type = comp.get("type")
        if comp_type not in {"module", "connector", "service", "script"}:
            continue
        mapping[comp["path"]] = (comp.get("version", ""), comp_type)
    return mapping


def extract_version(path: Path) -> str | None:
    """Extract ``__version__`` from ``path`` if present."""
    text = path.read_text()
    match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", text)
    return match.group(1) if match else None


def check_file(path: Path, expected: str) -> str | None:
    """Return error if ``path`` lacks ``__version__`` or mismatches ``expected``."""
    if path.is_dir():
        path = path / "__init__.py"
    if not path.exists():
        return f"Missing file: {path}"
    found = extract_version(path)
    if not found:
        return f"{path} missing __version__"
    if found != expected:
        return f"{path} has __version__ {found!r} but expected {expected!r}"
    return None


def gather_targets(
    args: Iterable[str], index_map: dict[str, tuple[str, str]]
) -> dict[Path, str]:
    """Return mapping of file paths to expected versions based on ``args``."""
    if args:
        targets: dict[Path, str] = {}
        for arg in args:
            rel = Path(arg).as_posix()
            if rel in index_map:
                targets[ROOT / rel] = index_map[rel][0]
        return targets
    return {ROOT / path: ver for path, (ver, _) in index_map.items()}


def main(argv: list[str] | None = None) -> int:
    """Entrypoint for version verification."""
    argv = argv or sys.argv[1:]
    index_map = load_index()
    targets = gather_targets(argv, index_map)
    errors = [check_file(path, ver) for path, ver in targets.items()]
    problems = [e for e in errors if e]
    if problems:
        for msg in problems:
            print(msg, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
