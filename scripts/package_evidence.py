"""Package rehearsal evidence into compressed archives with JSON manifests."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import tarfile
from pathlib import Path
from typing import Iterable

import hashlib

__version__ = "0.1.0"


def compute_sha256(path: Path) -> str:
    """Return the SHA-256 digest for *path*."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def list_files(source: Path) -> list[Path]:
    """Return a sorted list of files contained in *source*."""
    return sorted(
        path for path in source.rglob("*") if path.is_file() and not path.is_symlink()
    )


def build_archive(source: Path, output_dir: Path, bundle: str, timestamp: str) -> Path:
    """Create a gzip compressed tarball containing *source* files."""
    archive_name = f"{bundle}-{timestamp}.tar.gz"
    archive_path = output_dir / archive_name
    output_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "w:gz") as tar:
        for file_path in list_files(source):
            tar.add(file_path, arcname=file_path.relative_to(source))
    return archive_path


def build_manifest(
    *,
    bundle: str,
    source: Path,
    archive_path: Path,
    upload_base: str | None,
    timestamp: str,
) -> dict:
    """Construct the manifest payload for *bundle*."""
    files: list[dict[str, object]] = []
    for file_path in list_files(source):
        relative_path = str(file_path.relative_to(source))
        stat = file_path.stat()
        files.append(
            {
                "path": relative_path,
                "size_bytes": stat.st_size,
                "sha256": compute_sha256(file_path),
            }
        )

    archive_stat = archive_path.stat()
    upload_hint: str | None = None
    if upload_base:
        upload_hint = f"{upload_base.rstrip('/')}/{archive_path.name}"

    manifest: dict[str, object] = {
        "bundle": bundle,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": str(source),
        "archive": {
            "filename": archive_path.name,
            "size_bytes": archive_stat.st_size,
            "sha256": compute_sha256(archive_path),
            "content_type": "application/gzip",
            "upload_hint": upload_hint,
        },
        "files": files,
        "notes": [
            "Upload the generated archive to durable storage and share the upload URI",
            "Remove the local archive after upload to avoid accidental commits",
        ],
        "timestamp": timestamp,
    }
    return manifest


def write_manifest(manifest_path: Path, payload: dict) -> None:
    """Write *payload* as JSON to *manifest_path*."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    """Return the parsed command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", help="Logical name for the evidence bundle")
    parser.add_argument("source", help="Directory containing rehearsal evidence")
    parser.add_argument(
        "--output-dir",
        default="artifacts/evidence",
        help="Directory where the compressed archive will be written",
    )
    parser.add_argument(
        "--manifest",
        help=(
            "Path to the manifest JSON file "
            "(defaults to evidence_manifests/<bundle>.json)"
        ),
    )
    parser.add_argument(
        "--upload-base",
        help="Base URI where archives are uploaded (e.g. s3://bucket/path)",
    )
    parser.add_argument(
        "--skip-archive",
        action="store_true",
        help=(
            "Generate the manifest without creating a tarball "
            "(requires --archive-path)"
        ),
    )
    parser.add_argument(
        "--archive-path",
        help="Existing archive to reference when --skip-archive is used",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    """Entry-point for the evidence packaging workflow."""
    args = parse_args(argv)
    source = Path(args.source).resolve()
    if not source.exists():
        raise SystemExit(f"Source directory not found: {source}")
    if not source.is_dir():
        raise SystemExit(f"Source path must be a directory: {source}")

    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path(args.output_dir).resolve()

    if args.skip_archive:
        if not args.archive_path:
            raise SystemExit("--archive-path is required when --skip-archive is used")
        archive_path = Path(args.archive_path).resolve()
        if not archive_path.exists():
            raise SystemExit(f"Archive path not found: {archive_path}")
    else:
        archive_path = build_archive(source, output_dir, args.bundle, timestamp)

    manifest_path = (
        Path(args.manifest)
        if args.manifest
        else Path("evidence_manifests") / f"{args.bundle}.json"
    )

    manifest = build_manifest(
        bundle=args.bundle,
        source=source,
        archive_path=archive_path,
        upload_base=args.upload_base,
        timestamp=timestamp,
    )
    write_manifest(Path(manifest_path), manifest)

    if args.skip_archive:
        print(f"Manifest updated for existing archive: {manifest_path}")
    else:
        print(f"Created archive at {archive_path}")
        print(f"Manifest written to {manifest_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
