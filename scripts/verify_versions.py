#!/usr/bin/env python3
"""Compare module versions against component_index.json."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

__version__ = "0.4.0"

VERSION_RE = re.compile(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", re.MULTILINE)


def load_component_versions(index_path: Path) -> dict[Path, dict[str, str | None]]:
    data = json.loads(index_path.read_text(encoding="utf-8"))
    mapping: dict[Path, dict[str, str | None]] = {}
    for comp in data.get("components", []):
        mapping[Path(comp["path"])] = {
            "version": comp.get("version"),
            "status": comp.get("status"),
        }
    return mapping


def find_index_entry(
    rel_path: Path, mapping: dict[Path, dict[str, str | None]]
) -> dict[str, str | None] | None:
    for comp_path, version in mapping.items():
        if comp_path == rel_path:
            return version
        if comp_path.is_dir():
            try:
                rel_path.relative_to(comp_path)
            except ValueError:
                continue
            else:
                return version
    return None


def read_source_version(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return None
    match = VERSION_RE.search(text)
    return match.group(1) if match else None


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    index_mapping = load_component_versions(repo_root / "component_index.json")
    args = argv or sys.argv[1:]
    if args:
        paths = [Path(p) for p in args]
    else:
        env = os.getenv("PRE_COMMIT_FILES")
        if env:
            paths = [Path(p) for p in env.splitlines() if p]
        else:
            paths = [repo_root / p for p in index_mapping.keys()]

    errors: list[str] = []
    for path in paths:
        full_path = path if path.is_absolute() else repo_root / path
        if full_path.is_dir():
            full_path = full_path / "__init__.py"
        if full_path.suffix != ".py":
            continue
        rel = full_path.relative_to(repo_root)
        index_entry = find_index_entry(rel, index_mapping)
        if index_entry and index_entry.get("status") == "deprecated":
            continue
        source_version = read_source_version(full_path)
        if source_version is None:
            errors.append(f"{rel}: missing __version__")
            continue
        index_version = index_entry.get("version") if index_entry else None
        if index_version and index_version != source_version:
            errors.append(
                f"{rel}: __version__ {source_version} != "
                f"{index_version} in component_index.json"
            )

    for msg in errors:
        print(msg)
    return 1 if errors else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
