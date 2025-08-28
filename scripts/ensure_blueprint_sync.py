#!/usr/bin/env python3
"""Verify blueprint doc updates accompany core code changes."""
from __future__ import annotations

from pathlib import Path
import sys


BLUEPRINT = Path("docs/system_blueprint.md")


def main(paths: list[str]) -> int:
    """Return non-zero if blueprint was not updated alongside core changes."""
    changed = [Path(p) for p in paths]
    blueprint_touched = BLUEPRINT in changed

    def is_service_file(path: Path) -> bool:
        return path.suffix == ".py" and path.parent == Path(".")

    relevant = [p for p in changed if str(p).startswith("src/") or is_service_file(p)]

    if relevant and not blueprint_touched:
        files = "\n".join(str(p) for p in relevant)
        message = (
            "docs/system_blueprint.md must be updated when core files change:\n" + files
        )
        print(message, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
