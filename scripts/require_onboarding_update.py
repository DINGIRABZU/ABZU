"""Fail if key documents change without updating onboarding confirmation."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY_DOCS = ROOT / "docs" / "KEY_DOCUMENTS.md"
CONFIRM_PATH = ROOT / "onboarding_confirm.yml"
__version__ = "0.1.0"


def _protected_files() -> set[str]:
    """Return set of protected file paths from KEY_DOCUMENTS.md."""
    files: set[str] = set()
    pattern = re.compile(r"\(([^)]+)\)")
    in_table = False
    for line in KEY_DOCS.read_text().splitlines():
        if line.strip() == "## Protected Files":
            in_table = True
            continue
        if in_table:
            if not line.strip():
                break
            if line.startswith("| ["):
                match = pattern.search(line)
                if match:
                    path = (
                        (KEY_DOCS.parent / match.group(1)).resolve().relative_to(ROOT)
                    )
                    files.add(str(path))
    return files


def _staged_files() -> set[str]:
    """Return set of currently staged file paths."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        capture_output=True,
        text=True,
        check=False,
    )
    return set(result.stdout.split())


def main() -> int:
    """Exit with error if key docs changed without onboarding_confirm update."""
    staged = _staged_files()
    protected = _protected_files()
    touched = protected & staged
    if touched and "onboarding_confirm.yml" not in staged:
        print(
            "onboarding_confirm.yml must be updated when modifying key documents:",
            file=sys.stderr,
        )
        for path in sorted(touched):
            print(f"  {path}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
