"""Ensure Crown identity stays synchronized with doctrine updates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
from typing import Iterable, Sequence

__all__ = ["main"]
__version__ = "0.1.0"

ROOT = Path(__file__).resolve().parents[1]
IDENTITY_PATH = ROOT / "data" / "identity.json"
DOCTRINE_PATHS: Sequence[Path] = (
    ROOT / "docs" / "MISSION.md",
    ROOT / "docs" / "persona_api_guide.md",
    ROOT / "docs" / "The_Absolute_Protocol.md",
    ROOT / "docs" / "ABZU_blueprint.md",
    ROOT / "docs" / "awakening_overview.md",
)


@dataclass(frozen=True)
class Drift:
    """Doctrine file whose timestamp is newer than the identity summary."""

    path: Path
    doctrine_time: datetime
    identity_time: datetime

    def format(self) -> str:
        rel_path = self.path.relative_to(ROOT)
        doctrine_iso = self.doctrine_time.isoformat()
        identity_iso = self.identity_time.isoformat()
        return (
            f"{rel_path} updated {doctrine_iso} after data/identity.json "
            f"({identity_iso})"
        )


def _git_last_commit(path: Path) -> datetime | None:
    """Return the last git commit timestamp for *path* or ``None`` if unavailable."""

    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(path)],
            check=True,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    text = result.stdout.strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _has_uncommitted_changes(path: Path) -> bool:
    """Return ``True`` when *path* has staged or unstaged modifications."""

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--", str(path)],
            check=True,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    return bool(result.stdout.strip())


def _filesystem_mtime(path: Path) -> datetime | None:
    """Return the filesystem modification time as an aware datetime."""

    try:
        mtime = path.stat().st_mtime
    except FileNotFoundError:
        return None
    return datetime.fromtimestamp(mtime, tz=timezone.utc)


def _timestamp(path: Path) -> datetime | None:
    """Best effort timestamp for *path* using git history then filesystem data."""

    git_time = _git_last_commit(path)
    fs_time = _filesystem_mtime(path)
    if git_time is None:
        return fs_time
    if fs_time is None:
        return git_time
    if _has_uncommitted_changes(path):
        return max(git_time, fs_time)
    return git_time


def _missing_paths(paths: Iterable[Path]) -> list[Path]:
    """Return the subset of ``paths`` that do not exist on disk."""

    return [path for path in paths if not path.exists()]


def _detect_drift(
    identity_time: datetime, doctrine_paths: Iterable[Path]
) -> list[Drift]:
    """Return doctrine files whose timestamp is newer than the identity summary."""

    drifts: list[Drift] = []
    for path in doctrine_paths:
        doc_time = _timestamp(path)
        if doc_time is None:
            # Missing history or file—handled separately by missing path check.
            continue
        if doc_time > identity_time:
            drifts.append(
                Drift(
                    path=path,
                    doctrine_time=doc_time,
                    identity_time=identity_time,
                )
            )
    return drifts


def main() -> int:
    missing = _missing_paths([IDENTITY_PATH, *DOCTRINE_PATHS])
    if missing:
        for path in missing:
            rel = path.relative_to(ROOT)
            print(f"missing required file: {rel}", file=sys.stderr)
        if IDENTITY_PATH in missing:
            print(
                "Run `python scripts/refresh_crown_identity.py --use-stub` to"
                " regenerate the Crown identity summary.",
                file=sys.stderr,
            )
        return 1

    identity_time = _timestamp(IDENTITY_PATH)
    if identity_time is None:
        print(
            "unable to determine last refresh time for data/identity.json;"
            " run scripts/refresh_crown_identity.py",
            file=sys.stderr,
        )
        return 1

    drifts = _detect_drift(identity_time, DOCTRINE_PATHS)
    if drifts:
        for drift in drifts:
            print(drift.format(), file=sys.stderr)
        print(
            "Doctrine updates detected after the last identity refresh."
            " Run `python scripts/refresh_crown_identity.py --use-stub`",
            file=sys.stderr,
        )
        return 1

    print("check_identity_sync: identity is current with doctrine changes")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
