"""Shared fixtures for RAZAR handshake tests."""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

import pytest

IDENTITY_SUMMARY_TEXT: Final[str] = (
    "CROWN Identity Summary\n"
    "======================\n"
    "Designation: Crown Guardian\n"
    "Focus: Stabilize mission chains, maintain operator channels.\n"
    "Capabilities: triage, diagnostics, stabilization.\n"
)

# Freeze the modified timestamp so derived fingerprints remain deterministic.
FIXED_IDENTITY_MTIME: Final[int] = 1_704_067_200  # 2024-01-01T00:00:00Z
EXPECTED_IDENTITY_SHA256: Final[str] = hashlib.sha256(
    IDENTITY_SUMMARY_TEXT.encode("utf-8")
).hexdigest()
EXPECTED_IDENTITY_MODIFIED: Final[str] = datetime.fromtimestamp(
    FIXED_IDENTITY_MTIME, tz=timezone.utc
).isoformat()


@pytest.fixture
def identity_summary_file(tmp_path: Path) -> Path:
    """Write a deterministic identity summary for tests."""

    path = tmp_path / "identity_summary.json"
    path.write_text(IDENTITY_SUMMARY_TEXT, encoding="utf-8")
    os.utime(path, (FIXED_IDENTITY_MTIME, FIXED_IDENTITY_MTIME))
    return path


@pytest.fixture
def identity_fingerprint(identity_summary_file: Path) -> dict[str, str]:
    """Return the expected fingerprint for the synthetic identity summary."""

    digest = hashlib.sha256(identity_summary_file.read_bytes()).hexdigest()
    # Guard against accidental fixture drift.
    assert digest == EXPECTED_IDENTITY_SHA256
    return {
        "sha256": digest,
        "modified": EXPECTED_IDENTITY_MODIFIED,
    }


__all__ = [
    "identity_summary_file",
    "identity_fingerprint",
    "EXPECTED_IDENTITY_SHA256",
    "EXPECTED_IDENTITY_MODIFIED",
]
