#!/usr/bin/env python3
"""Scan connectors for placeholder markers and missing MCP adoption."""

from __future__ import annotations

__version__ = "0.1.0"

import re
import sys
from pathlib import Path


CONNECTORS_DIR = Path("connectors")
PLACEHOLDER_PATTERN = re.compile(r"\b(?:TODO|TBD)\b")
# Connectors that must adopt the ABZU_USE_MCP toggle.
MCP_REQUIRED = {"primordials_api.py", "mcp_gateway_example.py"}


def check_file(path: Path) -> list[str]:
    """Return a list of violation messages for ``path``."""

    violations: list[str] = []
    text = path.read_text(encoding="utf-8")

    for match in PLACEHOLDER_PATTERN.finditer(text):
        line = text[: match.start()].count("\n") + 1
        violations.append(f"{path}:{line} contains placeholder '{match.group(0)}'")

    if (
        path.name in MCP_REQUIRED
        and "ABZU_USE_MCP" not in text
        and "USE_MCP" not in text
    ):
        violations.append(f"{path} missing MCP adoption (ABZU_USE_MCP toggle)")

    return violations


def main() -> int:
    """Scan connectors and exit non-zero on violations."""

    problems: list[str] = []

    for file in CONNECTORS_DIR.rglob("*.py"):
        if file.name == "__init__.py":
            continue
        problems.extend(check_file(file))

    if problems:
        for msg in problems:
            print(msg, file=sys.stderr)
        return 1

    print("All connectors pass placeholder and MCP checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
