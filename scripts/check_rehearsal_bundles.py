"""Pre-commit guard ensuring rehearsal telemetry is packaged before commit."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List

HIGH_CHURN_DIRS = ("audio", "video", "emotion")
HIGH_CHURN_FILES = (
    Path("telemetry/events.jsonl"),
    Path("telemetry/media_manifest.json"),
)


def _load_manifest(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:  # noqa: PTH123
        return json.load(handle)


def _session_dirs(stage_root: Path) -> List[Path]:
    sessions: List[Path] = []
    for run_dir in stage_root.iterdir():
        if not run_dir.is_dir():  # noqa: PTH112
            continue
        rehearsal_dir = run_dir / "rehearsals"
        if not rehearsal_dir.exists():  # noqa: PTH113
            continue
        for session_dir in rehearsal_dir.iterdir():
            if session_dir.is_dir():  # noqa: PTH112
                sessions.append(session_dir)
    return sessions


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    stage_root = repo_root / "logs" / "stage_b"
    if not stage_root.exists():  # noqa: PTH113
        return 0

    problems: List[str] = []
    for session_dir in _session_dirs(stage_root):
        manifest_path = session_dir / "session_manifest.json"
        if not manifest_path.exists():  # noqa: PTH113
            problems.append(f"Missing manifest: {manifest_path}")

        for directory in HIGH_CHURN_DIRS:
            candidate = session_dir / directory
            if candidate.exists():  # noqa: PTH113
                has_files = any(candidate.rglob("*"))
                if has_files:
                    problems.append(f"High-churn telemetry still present: {candidate}")

        for rel_file in HIGH_CHURN_FILES:
            candidate_file = session_dir / rel_file
            if candidate_file.exists():  # noqa: PTH113
                problems.append(
                    f"High-churn telemetry file still present: {candidate_file}"
                )

        if manifest_path.exists():
            try:
                payload = _load_manifest(manifest_path)
            except Exception as exc:  # noqa: BLE001
                problems.append(f"Invalid manifest {manifest_path}: {exc}")
                continue
            bundle_info = payload.get("bundle", {})
            if not bundle_info.get("artifact_uri"):
                problems.append(f"Manifest missing artifact_uri: {manifest_path}")
            bundle_path = session_dir / "bundles" / bundle_info.get("name", "")
            if bundle_path.exists() and _is_tracked(bundle_path):  # noqa: PTH113
                problems.append(
                    "Bundle output {path} is tracked; remove it from Git and upload "
                    "to the evidence store.".format(path=bundle_path)
                )

    if problems:
        for issue in problems:
            print(issue)
        return 1
    return 0


def _is_tracked(path: Path) -> bool:
    try:
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
