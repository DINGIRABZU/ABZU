#!/usr/bin/env python3
"""Ensure required onboarding documents have been read."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIRM = ROOT / "onboarding_confirm.yml"
REQUIRED_DOCS = [
    "AGENTS.md",
    "docs/architecture_overview.md",
    "docs/project_overview.md",
    "docs/The_Absolute_Protocol.md",
    "docs/vector_memory.md",
    "docs/rag_pipeline.md",
    "docs/rag_music_oracle.md",
    "docs/vision_system.md",
    "docs/persona_api_guide.md",
    "docs/spiral_cortex_terminal.md",
]
__version__ = "0.1.0"


def sha256(path: Path) -> str:
    """Return the SHA256 hash of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    """Exit non-zero if onboarding confirmation is missing or outdated."""
    if not CONFIRM.exists():
        print(
            "Onboarding confirmation missing. "
            "Create 'onboarding_confirm.yml' in the repo root "
            "with hashes of required documents.",
            file=sys.stderr,
        )
        return 1

    try:
        data = yaml.safe_load(CONFIRM.read_text()) or {}
    except yaml.YAMLError as exc:
        print(f"Failed to parse {CONFIRM}: {exc}", file=sys.stderr)
        return 1

    docs: dict[str, dict[str, str]] = data.get("documents", {})

    missing_entries = [p for p in REQUIRED_DOCS if p not in docs]
    if missing_entries:
        print(
            "onboarding_confirm.yml missing entries for: " + ", ".join(missing_entries),
            file=sys.stderr,
        )
        return 1

    missing_files = []
    outdated = []
    for rel_path in REQUIRED_DOCS:
        info = docs.get(rel_path, {})
        if not isinstance(info, dict):
            outdated.append(rel_path)
            continue
        expected = info.get("sha256")
        if not expected:
            outdated.append(rel_path)
            continue
        path = ROOT / rel_path
        if not path.exists():
            missing_files.append(rel_path)
        elif sha256(path) != expected:
            outdated.append(rel_path)

    if missing_files or outdated:
        if missing_files:
            print("Missing documents: " + ", ".join(missing_files), file=sys.stderr)
        if outdated:
            print(
                "Documents have changed since confirmation: " + ", ".join(outdated),
                file=sys.stderr,
            )
        print(
            "Update onboarding_confirm.yml with new hashes after reviewing "
            "the documents.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
