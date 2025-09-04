#!/usr/bin/env python3
"""Verify release artifact checksums and signatures."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


def sha256_file(path: Path) -> str:
    """Return the SHA256 hex digest for *path*."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_signature(data: str, signature: str) -> bool:
    """Return True if *signature* is valid for *data*."""
    with tempfile.NamedTemporaryFile("w", delete=False) as sig_file:
        sig_file.write(signature)
        sig_file.flush()
        sig_path = Path(sig_file.name)
    with tempfile.NamedTemporaryFile("w", delete=False) as data_file:
        data_file.write(data)
        data_file.flush()
        data_path = Path(data_file.name)
    result = subprocess.run(
        ["gpg", "--verify", str(sig_path), str(data_path)], capture_output=True
    )
    sig_path.unlink(missing_ok=True)
    data_path.unlink(missing_ok=True)
    return result.returncode == 0


def main() -> None:
    """Validate artifacts listed in a manifest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "artifact_dir", type=Path, help="Directory containing artifacts"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("release/manifest.json"),
        help="Path to manifest.json",
    )
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    ok = True
    for name, info in manifest.get("files", {}).items():
        path = args.artifact_dir / name
        if not path.exists():
            print(f"Missing file: {name}")
            ok = False
            continue
        sha256 = sha256_file(path)
        if sha256 != info.get("sha256"):
            print(f"Checksum mismatch for {name}")
            ok = False
            continue
        if not verify_signature(sha256, info.get("signature", "")):
            print(f"Signature invalid for {name}")
            ok = False
    if not ok:
        raise SystemExit("Verification failed")
    print("All signatures valid.")


if __name__ == "__main__":
    main()
