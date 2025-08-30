from __future__ import annotations

"""Audit installed packages against pinned versions in ``pyproject.toml``."""

__version__ = "0.1.0"

import importlib.metadata as metadata
import sys
from pathlib import Path
from typing import Dict, List

try:  # pragma: no cover - py<3.11 fallback
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - py<3.11 fallback
    import tomli as tomllib

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _parse_requirements() -> Dict[str, str]:
    data = tomllib.loads(PYPROJECT.read_text())
    project = data.get("project", {})
    reqs: Dict[str, str] = {}
    for section in [
        project.get("dependencies", []),
        *project.get("optional-dependencies", {}).values(),
    ]:
        for entry in section:
            if "==" not in entry:
                continue
            name, version = entry.split("==", 1)
            reqs[name.lower()] = version
    return reqs


def audit() -> List[str]:
    mismatches: List[str] = []
    requirements = _parse_requirements()
    for pkg, expected_version in requirements.items():
        try:
            installed_version = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            mismatches.append(f"{pkg} not installed (expected {expected_version})")
            continue
        if installed_version != expected_version:
            # pragma: no cover - simple string
            mismatches.append(f"{pkg} {installed_version} != {expected_version}")
    return mismatches


def main() -> int:
    mismatches = audit()
    if mismatches:
        print("Dependency mismatches:")
        for line in mismatches:
            print(f"- {line}")
        return 1
    print("All dependencies match pinned versions.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    sys.exit(main())
