"""Release utilities for the project.

This script tags the current commit with the project version, builds a wheel,
and moves entries from the ``Unreleased`` section of ``CHANGELOG.md`` into a
newly dated release heading.
"""

from __future__ import annotations

import json
import subprocess
from datetime import date
from pathlib import Path

import tomllib

# Mapping of chakra names to associated module paths.
# Paths ending with a slash are treated as directory prefixes.
CHAKRA_MODULES: dict[str, list[str]] = {
    "root": ["server.py", "INANNA_AI/network_utils/"],
    "sacral": ["emotional_state.py", "emotion_registry.py"],
    "solar_plexus": ["learning_mutator.py", "state_transition_engine.py"],
    "heart": ["voice_avatar_config.yaml", "vector_memory.py"],
    "throat": ["crown_prompt_orchestrator.py", "INANNA_AI_AGENT/inanna_ai.py"],
    "third_eye": ["insight_compiler.py", "SPIRAL_OS/qnl_engine.py", "seven_dimensional_music.py"],
    "crown": ["init_crown_agent.py", "start_spiral_os.py", "crown_model_launcher.sh"],
}


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
    heading = (
        f"## [{version}] - {date.today().isoformat()}\n"
        "\n"
        "- Component health report: see `component_status.md`\n"
    )
    updated = text.replace("## [Unreleased]", f"## [Unreleased]\n\n{heading}")
    path.write_text(updated)


def tag_version(version: str) -> None:
    """Create a git tag for ``version``."""
    run(["git", "tag", f"v{version}"])


def build_wheel() -> None:
    """Build the project's wheel distribution."""
    run(["python", "-m", "build", "--wheel"])


def _changed_files() -> list[str]:
    """Return files changed since the last git tag.

    If no tag is found, fall back to listing tracked files.
    """
    try:
        tag = (
            subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        )
        diff = subprocess.run(
            ["git", "diff", "--name-only", f"{tag}..HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        files = [f for f in diff.splitlines() if f]
    except subprocess.CalledProcessError:
        files = (
            subprocess.run(
                ["git", "ls-files"], capture_output=True, text=True, check=True
            ).stdout.splitlines()
        )
    return files


def _chakra_changed(changed: list[str], paths: list[str]) -> bool:
    """Return ``True`` if any ``paths`` appear in ``changed`` files."""
    for p in paths:
        if p.endswith("/"):
            if any(f.startswith(p) for f in changed):
                return True
        else:
            if p in changed:
                return True
    return False


def bump_chakra_versions() -> None:
    """Increment versions for chakras with modified modules."""
    path = Path("docs/chakra_versions.json")
    if not path.exists():
        return
    versions = json.loads(path.read_text())
    changed = _changed_files()
    updated = False
    for chakra, modules in CHAKRA_MODULES.items():
        if _chakra_changed(changed, modules):
            major, minor, patch = map(int, versions[chakra].split("."))
            versions[chakra] = f"{major}.{minor}.{patch + 1}"
            updated = True
    if updated:
        path.write_text(json.dumps(versions, indent=2) + "\n")


def main() -> None:
    """Update changelog, tag the release and build a wheel."""
    bump_chakra_versions()
    version = get_version()
    update_changelog(version)
    tag_version(version)
    build_wheel()


if __name__ == "__main__":
    main()
