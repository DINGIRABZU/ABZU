#!/usr/bin/env python3
"""Verify blueprint doc updates accompany core architecture changes."""
from __future__ import annotations

__version__ = "0.2.0"

import subprocess
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = {
    ROOT / "docs" / "system_blueprint.md",
    ROOT / "docs" / "The_Absolute_Protocol.md",
    ROOT / "docs" / "blueprint_spine.md",
    ROOT / "docs" / "NEOABZU_spine.md",
}

REQUIRED_INDEXES = {
    ROOT / "docs" / "INDEX.md",
    ROOT / "docs" / "index.md",
}

ARCHITECTURE_PREFIXES: tuple[str, ...] = (
    "src/",
    "spiral_os/",
    "spiral_vector_db/",
    "memory/",
    "crown/",
    "NEOABZU/",
    "ai_core/",
    "agents/",
    "connectors/",
)

EXEMPT_ROOT_FILES = {"onboarding_confirm.yml"}


def _git_changed_files() -> set[Path]:
    """Return absolute paths reported by ``git status --porcelain``."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
            cwd=ROOT,
        )
    except OSError:
        return set()
    files: set[Path] = set()
    for line in result.stdout.splitlines():
        if not line:
            continue
        candidate = line[3:] if len(line) > 3 else line.strip()
        if not candidate:
            continue
        files.add((ROOT / candidate).resolve())
    return files


def _normalize(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    return path


def _is_architecture_change(path: Path) -> bool:
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        return False
    rel_posix = rel.as_posix()

    if rel_posix in EXEMPT_ROOT_FILES:
        return False

    if rel_posix.startswith("docs/") or rel_posix.startswith("tests/"):
        return False

    if any(rel_posix.startswith(prefix) for prefix in ARCHITECTURE_PREFIXES):
        # Skip documentation subtrees within architecture crates (e.g. NEOABZU/docs)
        parts = rel_posix.split("/")
        if len(parts) > 1 and parts[1] == "docs":
            return False
        return True

    # include root-level service files such as orchestration_master.py
    root_level = rel.parent == Path(".")
    allowed_suffix = rel.suffix in {
        ".py",
        ".rs",
        ".toml",
        ".yaml",
        ".yml",
    }
    return root_level and allowed_suffix


def main(paths: list[str]) -> int:
    """Return non-zero if architecture changes lack synchronized blueprint updates."""

    changed_paths = {_normalize(p) for p in paths}
    changed_paths |= _git_changed_files()
    if not changed_paths:
        return 0

    architecture_changes = [p for p in changed_paths if _is_architecture_change(p)]
    if not architecture_changes:
        return 0

    required = REQUIRED_DOCS | REQUIRED_INDEXES
    missing = [doc for doc in required if doc not in changed_paths]

    if missing:
        arch_rel = sorted(str(p.relative_to(ROOT)) for p in architecture_changes)
        missing_rel = sorted(str(p.relative_to(ROOT)) for p in missing)
        arch_list = "\n".join(arch_rel)
        missing_list = "\n".join(missing_rel)
        message = (
            "Architecture changes detected in:\n"
            f"{arch_list}\n"
            "The following blueprint documents and indexes must be updated:\n"
            f"{missing_list}"
        )
        print(message, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
