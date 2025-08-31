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
from collections.abc import Iterable

import tomllib

__version__ = "0.1.0"

# Mapping of chakra names to associated module paths.
# Paths ending with a slash are treated as directory prefixes.
CHAKRA_MODULES: dict[str, list[str]] = {
    "root": ["server.py", "INANNA_AI/network_utils/"],
    "sacral": ["emotional_state.py", "emotion_registry.py"],
    "solar_plexus": ["learning_mutator.py", "state_transition_engine.py"],
    "heart": ["voice_avatar_config.yaml", "vector_memory.py"],
    "throat": ["crown_prompt_orchestrator.py", "INANNA_AI_AGENT/inanna_ai.py"],
    "third_eye": [
        "insight_compiler.py",
        "SPIRAL_OS/qnl_engine.py",
        "seven_dimensional_music.py",
    ],
    "crown": ["init_crown_agent.py", "start_spiral_os.py", "crown_model_launcher.sh"],
}


def _verify_intent_log() -> None:
    """Ensure the latest commit is recorded in the change intent ledger."""
    ledger = Path("logs/change_intent.jsonl")
    if not ledger.exists():
        raise RuntimeError("logs/change_intent.jsonl is missing")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    with ledger.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip() and json.loads(line).get("commit_hash") == head:
                return
    raise RuntimeError(
        "Head commit not recorded in logs/change_intent.jsonl; "
        "run scripts/log_intent.py"
    )


def run(cmd: list[str]) -> None:
    """Run a command and ensure it succeeds."""
    subprocess.run(cmd, check=True)


def get_version() -> str:
    """Return the package version from ``pyproject.toml``."""
    data = tomllib.loads(Path("pyproject.toml").read_text())
    return data["project"]["version"]


def _record_unreleased_chakra_versions(updates: dict[str, str]) -> None:
    """Append chakra version bumps to the Unreleased changelog section."""
    if not updates:
        return
    path = Path("CHANGELOG.md")
    lines = path.read_text().splitlines(keepends=True)
    try:
        unreleased = next(
            i for i, line in enumerate(lines) if line.strip() == "## [Unreleased]"
        )
        chakra = next(
            i
            for i, line in enumerate(lines[unreleased:], start=unreleased)
            if line.strip() == "### Chakra Versions"
        )
    except StopIteration:
        return
    section_start = chakra + 1
    section_end = section_start
    while section_end < len(lines) and not (
        lines[section_end].startswith("### ") or lines[section_end].startswith("## ")
    ):
        section_end += 1
    section = lines[section_start:section_end]
    existing = {
        line.split(":")[0][2:]: idx
        for idx, line in enumerate(section)
        if line.startswith("- ") and ": " in line
    }
    for chakra_name, ver in updates.items():
        new_line = f"- {chakra_name}: {ver}\n"
        if chakra_name in existing:
            section[existing[chakra_name]] = new_line
        else:
            section.append(new_line)
    lines[section_start:section_end] = section
    path.write_text("".join(lines))


def _clear_unreleased_chakra_versions(chakras: Iterable[str]) -> None:
    """Remove chakra version entries from the Unreleased section."""
    if not chakras:
        return
    path = Path("CHANGELOG.md")
    lines = path.read_text().splitlines(keepends=True)
    try:
        unreleased = next(
            i for i, line in enumerate(lines) if line.strip() == "## [Unreleased]"
        )
        chakra = next(
            i
            for i, line in enumerate(lines[unreleased:], start=unreleased)
            if line.strip() == "### Chakra Versions"
        )
    except StopIteration:
        return
    section_start = chakra + 1
    section_end = section_start
    while section_end < len(lines) and not (
        lines[section_end].startswith("### ") or lines[section_end].startswith("## ")
    ):
        section_end += 1
    section = [
        line
        for line in lines[section_start:section_end]
        if not any(line.startswith(f"- {c}:") for c in chakras)
    ]
    lines[section_start:section_end] = section
    path.write_text("".join(lines))


def update_changelog(version: str, chakra_updates: dict[str, str]) -> None:
    """Insert a release heading into ``CHANGELOG.md``.

    ``chakra_updates`` maps chakra names to their new semantic versions.
    """
    path = Path("CHANGELOG.md")
    if chakra_updates:
        _clear_unreleased_chakra_versions(chakra_updates.keys())
    text = path.read_text()
    lines = [f"## [{version}] - {date.today().isoformat()}\n", "\n"]
    if chakra_updates:
        lines.append("### Chakra Versions\n")
        lines.extend(f"- {chakra}: {ver}\n" for chakra, ver in chakra_updates.items())
        lines.append("\n")
    lines.append("- Component health report: see `component_status.md`\n")
    heading = "".join(lines)
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
        tag = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        diff = subprocess.run(
            ["git", "diff", "--name-only", f"{tag}..HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        files = [f for f in diff.splitlines() if f]
    except subprocess.CalledProcessError:
        files = subprocess.run(
            ["git", "ls-files"], capture_output=True, text=True, check=True
        ).stdout.splitlines()
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


def bump_chakra_versions() -> dict[str, str]:
    """Increment versions for chakras with modified modules.

    Returns a mapping of chakra names to their updated versions. If the
    version file does not exist it is created with ``1.0.0`` for each chakra
    and an empty mapping is returned.
    """
    path = Path("docs/chakra_versions.json")
    if not path.exists():
        path.write_text(
            json.dumps({c: "1.0.0" for c in CHAKRA_MODULES}, indent=2) + "\n"
        )
        return {}
    versions = json.loads(path.read_text())
    changed_files = _changed_files()
    updates: dict[str, str] = {}
    for chakra, modules in CHAKRA_MODULES.items():
        if _chakra_changed(changed_files, modules):
            major, minor, patch = map(int, versions[chakra].split("."))
            new_version = f"{major}.{minor}.{patch + 1}"
            versions[chakra] = new_version
            updates[chakra] = new_version
    if updates:
        path.write_text(json.dumps(versions, indent=2) + "\n")
        _record_unreleased_chakra_versions(updates)
    return updates


def main() -> None:
    """Update changelog, tag the release and build a wheel."""
    _verify_intent_log()
    chakra_updates = bump_chakra_versions()
    version = get_version()
    update_changelog(version, chakra_updates)
    tag_version(version)
    build_wheel()


if __name__ == "__main__":
    main()
