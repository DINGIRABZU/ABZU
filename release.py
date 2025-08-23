"""Release utilities for the project.

This script tags the current commit with the project version, builds a wheel,
and moves entries from the ``Unreleased`` section of ``CHANGELOG.md`` into a
newly dated release heading.
"""

from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

import tomllib


def run(cmd: list[str]) -> None:
    """Run a command and ensure it succeeds."""
    subprocess.run(cmd, check=True)


def get_version() -> str:
    """Return the package version from ``pyproject.toml``."""
    data = tomllib.loads(Path("pyproject.toml").read_text())
    return data["project"]["version"]


def update_changelog(version: str) -> None:
    """Insert a release heading into ``CHANGELOG.md``."""
    path = Path("CHANGELOG.md")
    text = path.read_text()
    heading = f"## [{version}] - {date.today().isoformat()}"
    updated = text.replace("## [Unreleased]", f"## [Unreleased]\n\n{heading}")
    path.write_text(updated)


def tag_version(version: str) -> None:
    """Create a git tag for ``version``."""
    run(["git", "tag", f"v{version}"])


def build_wheel() -> None:
    """Build the project's wheel distribution."""
    run(["python", "-m", "build", "--wheel"])


def main() -> None:
    """Update changelog, tag the release and build a wheel."""
    version = get_version()
    update_changelog(version)
    tag_version(version)
    build_wheel()


if __name__ == "__main__":
    main()
