"""Shared helpers for contract placeholder test suites.

These utilities keep fixture loading consistent across the contract
placeholders while we wait for hardware-backed telemetry. Modules should rely
on :func:`load_contract_fixture` to read JSON assets so missing bundles are
skipped gracefully in sandbox-only runs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES_ROOT = Path(__file__).resolve().parents[1] / "fixtures"

HARDWARE_TODO_NOTE = (
    "TODO hardware replay: replace placeholder assertions once the Neo-APSU "
    "contracts replay on hardware runners."
)


def load_contract_fixture(*relative_path: str) -> dict[str, Any]:
    """Return a JSON fixture under :data:`FIXTURES_ROOT` or skip if missing."""

    fragment = Path(*relative_path)
    fixture_path = FIXTURES_ROOT / fragment
    if not fixture_path.exists():
        pytest.skip(
            "environment-limited: missing fixture "
            f"{fragment.as_posix()} (" + HARDWARE_TODO_NOTE + ")"
        )
    return json.loads(fixture_path.read_text(encoding="utf-8"))
