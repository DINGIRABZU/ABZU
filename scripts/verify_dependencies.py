#!/usr/bin/env python3
"""Validate dependencies against docs/dependency_registry.md."""
from __future__ import annotations

__version__ = "0.1.0"

import re
import sys
from pathlib import Path
from typing import Dict

REGISTRY = Path("docs/dependency_registry.md")
REQS = Path("requirements.txt")
POETRY_LOCK = Path("poetry.lock")


def parse_registry() -> Dict[str, str]:
    """Return mapping of package name to approved version."""
    entries: Dict[str, str] = {}
    if not REGISTRY.exists():
        return entries
    for line in REGISTRY.read_text().splitlines():
        if line.startswith("|") and not line.startswith("| Name"):
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) >= 3:
                name, _min_version, approved = parts[:3]
                entries[name.lower()] = approved
    return entries


def parse_requirements() -> Dict[str, str]:
    """Return dependency versions from requirements.txt."""
    deps: Dict[str, str] = {}
    if not REQS.exists():
        return deps
    pattern = re.compile(r"^([A-Za-z0-9_.-]+)==([A-Za-z0-9_.-]+)$")
    for line in REQS.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = pattern.match(line)
        if match:
            deps[match.group(1).lower()] = match.group(2)
    return deps


def parse_poetry_lock() -> Dict[str, str]:
    """Return dependency versions from poetry.lock if present."""
    deps: Dict[str, str] = {}
    if not POETRY_LOCK.exists():
        return deps
    content = POETRY_LOCK.read_text()
    for block in content.split("[[package]]"):
        name_match = re.search(r'name = "([^"]+)"', block)
        ver_match = re.search(r'version = "([^"]+)"', block)
        if name_match and ver_match:
            deps[name_match.group(1).lower()] = ver_match.group(2)
    return deps


def main() -> int:
    """Validate requirements and exit with non-zero status on mismatch."""
    registry = parse_registry()
    combined = parse_requirements()
    poetry_deps = parse_poetry_lock()

    for pkg, ver in poetry_deps.items():
        if pkg in combined and combined[pkg] != ver:
            msg = (
                "Version mismatch between requirements.txt and poetry.lock "
                f"for {pkg}: {combined[pkg]} vs {ver}"
            )
            print(msg)
            return 1
        combined.setdefault(pkg, ver)

    missing = []
    mismatched = []
    for pkg, ver in combined.items():
        reg_ver = registry.get(pkg)
        if reg_ver is None:
            missing.append(pkg)
        elif reg_ver != ver:
            mismatched.append(f"{pkg} (registry {reg_ver} != {ver})")

    if missing:
        print("Dependencies missing from registry: " + ", ".join(sorted(missing)))
    if mismatched:
        print("Version mismatches: " + ", ".join(mismatched))

    if missing or mismatched:
        return 1

    print("Dependencies verified against registry.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
