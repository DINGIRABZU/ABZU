from __future__ import annotations

"""Ensure connector registry updates accompany connector changes.

If any tracked connector source files are staged for commit, this hook
requires ``docs/connectors/CONNECTOR_INDEX.md`` to be included in the
staged files as well. Tracked connector paths are derived from the
``code`` column of the registry so the check automatically adapts when
new connectors are registered.
"""

__version__ = "0.1.0"

from pathlib import Path
import re
import subprocess
import sys

INDEX_PATH = Path("docs/connectors/CONNECTOR_INDEX.md")


def get_staged_files() -> list[str]:
    """Return a list of staged files relative to repo root."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.splitlines()


def parse_connector_paths(index_text: str) -> set[str]:
    """Extract connector source paths from the registry table."""
    paths: set[str] = set()
    for line in index_text.splitlines():
        if not line.startswith("|") or line.startswith("| id "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 8:
            continue
        code_cell = cells[7]
        match = re.search(r"\(([^)]+)\)", code_cell)
        if not match:
            continue
        rel_path = match.group(1)
        abs_path = (INDEX_PATH.parent / rel_path).resolve()
        try:
            paths.add(str(abs_path.relative_to(Path.cwd())))
        except ValueError:
            # If path cannot be made relative, skip it
            continue
    return paths


def main() -> int:
    staged = set(get_staged_files())
    if not staged:
        return 0
    try:
        index_text = INDEX_PATH.read_text()
    except FileNotFoundError:
        print(f"Missing {INDEX_PATH}", file=sys.stderr)
        return 1
    connector_paths = parse_connector_paths(index_text)
    touched_connectors = connector_paths.intersection(staged)
    if touched_connectors and str(INDEX_PATH) not in staged:
        files = "\n".join(sorted(touched_connectors))
        message = (
            "docs/connectors/CONNECTOR_INDEX.md must be updated when "
            "connector files change:\n" + files
        )
        print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
