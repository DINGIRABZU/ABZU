#!/usr/bin/env python3
"""Validate registered component versions against requirements files."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict

__version__ = "0.1.0"

COMPONENT_INDEX = Path("component_index.json")
REQ_TXT = Path("requirements.txt")
REQ_LOCK = Path("requirements.lock")

PINNED_RE = re.compile(r"^([A-Za-z0-9_.-]+)==([A-Za-z0-9_.-]+)")


def parse_requirements(path: Path) -> Dict[str, str]:
    """Return mapping of package name to pinned version."""
    deps: Dict[str, str] = {}
    if not path.exists():
        return deps
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = PINNED_RE.match(line)
        if match:
            deps[match.group(1).lower()] = match.group(2)
    return deps


def load_components(path: Path) -> Dict[str, str]:
    """Load component versions from component_index.json."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {c["id"].lower(): c["version"] for c in data.get("components", [])}


def main() -> int:
    components = load_components(COMPONENT_INDEX)
    reqs = parse_requirements(REQ_TXT)
    lock_reqs = parse_requirements(REQ_LOCK)

    mismatches: list[str] = []
    for name, version in components.items():
        req_version = reqs.get(name) or lock_reqs.get(name)
        if req_version and req_version != version:
            mismatches.append(f"{name}: {version} != {req_version}")

    if mismatches:
        print("Component version mismatches detected:\n" + "\n".join(mismatches))
        return 1

    print("Component versions match requirements.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
