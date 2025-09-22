"""Validate rehearsal evidence manifests and enforce archive policy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

__version__ = "0.1.0"

REQUIRED_ROOT_KEYS = {"bundle", "created_at", "source", "archive", "files", "timestamp"}
REQUIRED_ARCHIVE_KEYS = {
    "filename",
    "size_bytes",
    "sha256",
    "content_type",
    "upload_hint",
}
REQUIRED_FILE_KEYS = {"path", "size_bytes", "sha256"}


class ManifestValidationError(Exception):
    """Raised when a manifest fails validation."""


def _load_manifest(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise ManifestValidationError(f"Invalid JSON in {path}: {exc}") from exc


def _validate_archive(archive: dict, *, require_upload_hint: bool) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_ARCHIVE_KEYS - archive.keys()
    if missing:
        errors.append(f"Archive section missing keys: {sorted(missing)}")

    sha256 = archive.get("sha256")
    if not isinstance(sha256, str) or len(sha256) != 64:
        errors.append("Archive sha256 must be a 64 character hexadecimal string")

    size = archive.get("size_bytes")
    if not isinstance(size, int) or size <= 0:
        errors.append("Archive size_bytes must be a positive integer")

    content_type = archive.get("content_type")
    if content_type not in {"application/gzip", "application/zstd"}:
        errors.append("Archive content_type must describe a compressed payload")

    upload_hint = archive.get("upload_hint")
    if require_upload_hint and not upload_hint:
        errors.append("Archive upload_hint is required in CI enforcement mode")
    return errors


def _validate_file_entries(files: list[dict]) -> list[str]:
    errors: list[str] = []
    if not files:
        return ["Files array must include at least one entry"]

    for entry in files:
        missing = REQUIRED_FILE_KEYS - entry.keys()
        if missing:
            errors.append(f"File entry missing keys {sorted(missing)}: {entry}")
            continue
        if not isinstance(entry["path"], str):
            errors.append(f"File path must be a string: {entry}")
        if not isinstance(entry["size_bytes"], int) or entry["size_bytes"] <= 0:
            errors.append(f"File size_bytes must be positive: {entry}")
        sha256 = entry.get("sha256")
        if not isinstance(sha256, str) or len(sha256) != 64:
            errors.append(f"File sha256 must be 64 hex characters: {entry}")
    return errors


def validate_manifest(path: Path, *, require_upload_hint: bool) -> list[str]:
    payload = _load_manifest(path)
    errors: list[str] = []

    missing = REQUIRED_ROOT_KEYS - payload.keys()
    if missing:
        errors.append(f"Missing top-level keys: {sorted(missing)}")

    archive = payload.get("archive", {})
    if not isinstance(archive, dict):
        errors.append("Archive section must be a JSON object")
    else:
        errors.extend(
            _validate_archive(archive, require_upload_hint=require_upload_hint)
        )

    files = payload.get("files", [])
    if not isinstance(files, list):
        errors.append("Files section must be a list")
    else:
        errors.extend(_validate_file_entries(files))

    timestamp = payload.get("timestamp")
    if not isinstance(timestamp, str) or not timestamp:
        errors.append("Timestamp must be a non-empty string")

    source = payload.get("source")
    if not isinstance(source, str) or not source:
        errors.append("Source must be a non-empty string")

    return errors


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        default=["evidence_manifests"],
        help="Manifest files or directories to validate",
    )
    parser.add_argument(
        "--require-upload-hint",
        action="store_true",
        help="Fail if archive.upload_hint is missing",
    )
    return parser.parse_args(argv)


def iter_manifest_files(paths: list[str]) -> list[Path]:
    manifests: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            manifests.extend(sorted(path.glob("*.json")))
        elif path.suffix == ".json":
            manifests.append(path)
    return manifests


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    manifests = iter_manifest_files(args.paths)
    if not manifests:
        print("No manifest files found", flush=True)
        return 0

    failures = False
    for manifest_path in manifests:
        errors = validate_manifest(
            manifest_path, require_upload_hint=args.require_upload_hint
        )
        if errors:
            failures = True
            print(f"Errors in {manifest_path}:")
            for error in errors:
                print(f"  - {error}")
    return 1 if failures else 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
