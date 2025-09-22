"""Utility for bundling rehearsal telemetry into uploadable artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import tarfile
from pathlib import Path
from typing import Iterable, List, Sequence

DEFAULT_HIGH_CHURN_PATHS: Sequence[Path] = (
    Path("audio"),
    Path("video"),
    Path("emotion"),
    Path("telemetry/events.jsonl"),
    Path("telemetry/media_manifest.json"),
)


class PackagingError(RuntimeError):
    """Raised when packaging cannot be completed."""


def _utc_now() -> str:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    return now.isoformat().replace("+00:00", "Z")


def _iter_existing_paths(base: Path, relative_paths: Sequence[Path]) -> List[Path]:
    existing: List[Path] = []
    for rel in relative_paths:
        candidate = base / rel
        if candidate.exists():
            existing.append(candidate)
    return existing


def _add_to_archive(archive: tarfile.TarFile, base: Path, path: Path) -> None:
    arcname = path.relative_to(base)
    archive.add(path, arcname=str(arcname))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:  # noqa: PTH123
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ensure_bundle_dir(session_path: Path) -> Path:
    bundle_dir = session_path / "bundles"
    bundle_dir.mkdir(exist_ok=True)
    return bundle_dir


def _bundle_name(session_path: Path) -> str:
    return f"{session_path.name}_media.tar.gz"


def _compose_artifact_uri(
    artifact_base_uri: str, stage: str, run_id: str, session: str, bundle_name: str
) -> str:
    prefix = artifact_base_uri.rstrip("/")
    return f"{prefix}/{stage}/{run_id}/{session}/{bundle_name}"


def _relative_strings(base: Path, paths: Iterable[Path]) -> List[str]:
    return [str(p.relative_to(base)) for p in paths]


def package_session(
    session_path: Path,
    artifact_base_uri: str,
    high_churn_paths: Sequence[Path] = DEFAULT_HIGH_CHURN_PATHS,
    prune: bool = False,
) -> dict:
    if not session_path.is_dir():  # noqa: PTH112
        raise PackagingError(
            f"Session path {session_path} does not exist or is not a directory"
        )

    run_dir = session_path.parent.parent
    stage_dir = run_dir.parent
    stage_name = stage_dir.name
    run_id = run_dir.name
    session_name = session_path.name

    bundle_dir = _ensure_bundle_dir(session_path)
    bundle_name = _bundle_name(session_path)
    bundle_path = bundle_dir / bundle_name

    targets = _iter_existing_paths(session_path, high_churn_paths)
    if not targets:
        raise PackagingError("No high-churn telemetry paths found. Nothing to package.")

    with tarfile.open(bundle_path, "w:gz") as archive:
        for target in targets:
            _add_to_archive(archive, session_path, target)

    checksum = _sha256(bundle_path)
    size_bytes = bundle_path.stat().st_size

    artifact_uri = _compose_artifact_uri(
        artifact_base_uri, stage_name, run_id, session_name, bundle_name
    )

    manifest_payload = {
        "version": 1,
        "stage": stage_name,
        "run_id": run_id,
        "session": session_name,
        "generated_at": _utc_now(),
        "bundle": {
            "name": bundle_name,
            "artifact_uri": artifact_uri,
            "sha256": checksum,
            "size_bytes": size_bytes,
            "sources": _relative_strings(session_path, targets),
        },
        "retained_files": sorted(
            _relative_strings(
                session_path,
                [
                    p
                    for p in session_path.iterdir()
                    if p.name not in {"audio", "video", "emotion", "bundles"}
                ],
            )
        ),
    }

    manifest_path = session_path / "session_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest_payload, indent=2) + "\n",
        encoding="utf-8",
    )

    _update_run_manifest(session_path.parent, manifest_payload)

    if prune:
        _prune_targets(targets)

    return {
        "bundle_path": bundle_path,
        "manifest_path": manifest_path,
        "artifact_uri": artifact_uri,
    }


def _update_run_manifest(rehearsal_dir: Path, session_payload: dict) -> None:
    manifest_path = rehearsal_dir / "rehearsal_manifest.json"
    data = {
        "version": 1,
        "stage": rehearsal_dir.parent.parent.name,
        "run_id": rehearsal_dir.parent.name,
        "sessions": {},
    }
    if manifest_path.exists():  # noqa: PTH113
        with manifest_path.open("r", encoding="utf-8") as existing:  # noqa: PTH123
            data = json.load(existing)
    if "sessions" not in data:
        data["sessions"] = {}
    data["sessions"][session_payload["session"]] = session_payload["bundle"]
    data["updated_at"] = _utc_now()
    manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _prune_targets(targets: Sequence[Path]) -> None:
    for target in targets:
        if target.is_dir():  # noqa: PTH112
            for child in sorted(target.rglob("*"), reverse=True):
                if child.is_file():  # noqa: PTH113
                    child.unlink()
                elif child.is_dir():  # noqa: PTH112
                    child.rmdir()
            target.rmdir()
        elif target.is_file():  # noqa: PTH113
            target.unlink()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "session_paths",
        nargs="+",
        type=Path,
        help="One or more rehearsal session directories to package.",
    )
    parser.add_argument(
        "--artifact-base-uri",
        default=os.getenv("EVIDENCE_BASE_URI", "evidence://stage-b"),
        help="Base URI for artifact uploads used in manifests.",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Remove packaged telemetry from the working tree after bundling.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    errors: List[str] = []
    for session_path in args.session_paths:
        try:
            package_session(
                session_path=session_path,
                artifact_base_uri=args.artifact_base_uri,
                prune=args.prune,
            )
        except PackagingError as exc:
            errors.append(f"{session_path}: {exc}")
    if errors:
        joined = "\n".join(errors)
        raise SystemExit(f"Packaging failed:\n{joined}")


if __name__ == "__main__":
    main()
