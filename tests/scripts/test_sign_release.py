from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def _generate_key(env: dict[str, str]) -> None:
    subprocess.run(
        [
            "gpg",
            "--batch",
            "--passphrase",
            "",
            "--quick-gen-key",
            "test@example.com",
        ],
        check=True,
        env=env,
    )


def test_sign_and_verify(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "dist"
    artifact_dir.mkdir()
    artifact = artifact_dir / "file.txt"
    artifact.write_text("hello")

    gnupg_home = tmp_path / "gnupg"
    gnupg_home.mkdir()
    os.chmod(gnupg_home, 0o700)
    env = {**os.environ, "GNUPGHOME": str(gnupg_home)}
    _generate_key(env)

    manifest = tmp_path / "manifest.json"
    subprocess.run(
        [
            sys.executable,
            "scripts/sign_release.py",
            str(artifact_dir),
            "--key-id",
            "test@example.com",
            "--manifest",
            str(manifest),
        ],
        check=True,
        env=env,
    )

    data = json.loads(manifest.read_text())
    info = data["files"][artifact.name]
    expected = hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert info["sha256"] == expected
    assert "BEGIN PGP SIGNATURE" in info["signature"]

    subprocess.run(
        [
            sys.executable,
            "scripts/verify_release_signature.py",
            str(artifact_dir),
            "--manifest",
            str(manifest),
        ],
        check=True,
        env=env,
    )
