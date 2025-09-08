from __future__ import annotations

"""Ensure documentation registry timestamps and feature references are current."""

from pathlib import Path
from datetime import datetime
import subprocess
import sys

__version__ = "0.1.0"

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "docs" / "doctrine_index.md"
FEATURES_DIR = ROOT / "docs" / "features"
CANONICAL_DOCS = [
    ROOT / "docs" / "INDEX.md",
    ROOT / "docs" / "index.md",
    ROOT / "docs" / "BLUEPRINT_EXPORT.md",
]


def _parse_index(path: Path) -> list[tuple[Path, datetime]]:
    """Return pairs of file paths and recorded update times from doctrine index."""
    entries: list[tuple[Path, datetime]] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        if not line.startswith("|"):
            continue
        parts = [part.strip() for part in line.strip().split("|")[1:-1]]
        if len(parts) != 4 or parts[0] == "File":
            continue
        file_rel, _version, _checksum, updated = parts
        try:
            ts = datetime.fromisoformat(updated)
        except ValueError:
            continue
        entries.append((ROOT / file_rel, ts))
    return entries


def _git_last_commit(path: Path) -> datetime | None:
    """Return last commit time for *path* as a datetime or None if unavailable."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(path)],
            capture_output=True,
            text=True,
            check=True,
            cwd=ROOT,
        )
    except subprocess.CalledProcessError:
        return None
    text = result.stdout.strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _check_doctrine_index() -> list[str]:
    """Validate doctrine index timestamps against git commit history."""
    if not INDEX_PATH.exists():
        return ["missing docs/doctrine_index.md"]
    errors: list[str] = []
    for file_path, recorded_time in _parse_index(INDEX_PATH):
        if not file_path.exists():
            errors.append(
                f"{file_path.relative_to(ROOT)} listed in doctrine_index.md but missing"
            )
            continue
        commit_time = _git_last_commit(file_path)
        if commit_time and commit_time > recorded_time:
            rel = file_path.relative_to(ROOT)
            errors.append(
                f"{rel} updated {commit_time.isoformat()} after index timestamp "
                f"{recorded_time.isoformat()}"
            )
    return errors


def _check_feature_refs() -> list[str]:
    """Ensure each feature spec is referenced in a canonical document."""
    if not FEATURES_DIR.exists():
        return []
    doc_texts = [
        doc.read_text(encoding="utf-8") for doc in CANONICAL_DOCS if doc.exists()
    ]
    errors: list[str] = []
    for feature in FEATURES_DIR.glob("*.md"):
        if feature.name in {"README.md", "FEATURE_TEMPLATE.md"}:
            continue
        name = feature.name
        if not any(name in text for text in doc_texts):
            errors.append(f"{name} not referenced in canonical docs")
    return errors


def main() -> int:
    errors = _check_doctrine_index()
    errors.extend(_check_feature_refs())
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print("verify_docs_up_to_date: all checks passed")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
