#!/usr/bin/env python3
"""Fail if required tools or packages are missing."""
from __future__ import annotations

import importlib.util
import shutil
import sys
from typing import Dict

REQUIRED_PACKAGES: Dict[str, str] = {
    "pyyaml": "yaml",
    "prometheus_client": "prometheus_client",
    "websockets": "websockets",
}
REQUIRED_TOOLS = ["pyenv"]
__version__ = "0.1.0"


def check_packages() -> list[str]:
    """Return a list of missing Python packages."""
    missing: list[str] = []
    for name, module in REQUIRED_PACKAGES.items():
        if importlib.util.find_spec(module) is None:
            missing.append(name)
    return missing


def check_tools() -> list[str]:
    """Return a list of missing command line tools."""
    return [tool for tool in REQUIRED_TOOLS if shutil.which(tool) is None]


def main() -> int:
    """Exit non-zero when prerequisites are missing."""
    missing_packages = check_packages()
    missing_tools = check_tools()
    if missing_packages:
        print(
            "Missing Python packages: " + ", ".join(missing_packages),
            file=sys.stderr,
        )
    if missing_tools:
        print(
            "Missing required tools: " + ", ".join(missing_tools),
            file=sys.stderr,
        )
    if missing_packages or missing_tools:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
