"""Require changelog and component index updates when new modules are added."""

from __future__ import annotations

__version__ = "0.1.0"

import subprocess
import sys

REQUIRED_DOCS = {"CHANGELOG.md", "docs/component_index.md"}


def get_staged_changes() -> list[tuple[str, str]]:
    """Return (status, path) for staged files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-status"],
        check=True,
        capture_output=True,
        text=True,
    )
    entries: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        status, path = line.split(maxsplit=1)
        entries.append((status, path))
    return entries


def main() -> int:
    staged = get_staged_changes()
    added_modules = [
        p for s, p in staged if s == "A" and p.startswith("src/") and p.endswith(".py")
    ]
    if not added_modules:
        return 0
    touched = {p for _, p in staged}
    missing = REQUIRED_DOCS.difference(touched)
    if missing:
        files = "\n".join(sorted(added_modules))
        msg = (
            "New modules detected:\n"
            f"{files}\n"
            "Add entries to CHANGELOG.md and docs/component_index.md."
        )
        print(msg, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
