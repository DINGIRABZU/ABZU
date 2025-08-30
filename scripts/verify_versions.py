#!/usr/bin/env python3
"""Ensure source versions match component_index.json."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

__version__ = "0.2.0"

VERSION_RE = re.compile(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", re.MULTILINE)


def load_component_versions(index_path: Path) -> dict[Path, str]:
    data = json.loads(index_path.read_text(encoding="utf-8"))
    mapping: dict[Path, str] = {}
    for comp in data.get("components", []):
        mapping[Path(comp["path"])] = comp["version"]
    return mapping


def find_index_version(rel_path: Path, mapping: dict[Path, str]) -> str | None:
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
    paths = [Path(p) for p in (argv or sys.argv[1:])]

    errors: list[str] = []
    for path in paths:
        if path.suffix != ".py":
            continue
        full_path = path if path.is_absolute() else repo_root / path
        source_version = read_source_version(full_path)
        rel = full_path.relative_to(repo_root)
        if source_version is None:
            errors.append(f"{rel}: missing __version__")
            continue
        index_version = find_index_version(rel, index_mapping)
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
