#!/usr/bin/env python3
"""Generate SHA256 checksums for build artifacts and sign them with GPG.

The resulting hashes and signatures are written to a manifest file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha256_file(path: Path) -> str:
    """Return the SHA256 hex digest for *path*."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sign_data(data: str, key_id: str) -> str:
    """Return an ASCII-armored detached signature of *data* using *key_id*."""
    proc = subprocess.run(
        [
            "gpg",
            "--armor",
            "--batch",
            "--yes",
            "--local-user",
            key_id,
            "--detach-sign",
            "--output",
            "-",
        ],
        input=data.encode(),
        check=True,
        capture_output=True,
    )
    return proc.stdout.decode()


def main() -> None:
    """Create a manifest with checksums and signatures for build artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "artifact_dir", type=Path, help="Directory containing artifacts"
    )
    parser.add_argument("--key-id", required=True, help="GPG key ID or fingerprint")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("release/manifest.json"),
        help="Output manifest path",
    )
    args = parser.parse_args()

    manifest: dict[str, dict[str, str]] = {}
    for path in sorted(args.artifact_dir.iterdir()):
        if path.name == args.manifest.name or not path.is_file():
            continue
        sha256 = sha256_file(path)
        signature = sign_data(sha256, args.key_id)
        manifest[path.name] = {"sha256": sha256, "signature": signature}

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps({"files": manifest}, indent=2))
    print(f"Wrote manifest to {args.manifest}")


if __name__ == "__main__":
    main()
