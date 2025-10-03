"""Stub coverage for the identity contract bootstrap evidence.

These checks mirror ``docs/contracts/identity.md`` and the
``identity_loader.py`` entry in ``docs/apsu_migration_matrix.md``. When the
Neo-APSU identity bindings are available, extend the tests to verify the
PyO3 bridge, handshake acknowledgements, and telemetry hashes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
_BASELINE = _FIXTURES / "chroma_baseline" / "baseline.json"


def test_identity_vector_fixture_shape() -> None:
    """Check the vector baseline used by identity ingestion."""

    payload = json.loads(_BASELINE.read_text(encoding="utf-8"))
    assert payload["collection"] == "spiral_vectors"
    records = payload["records"]
    assert isinstance(records, list) and records
    for record in records:
        assert {"id", "embedding", "metadata"} <= set(record)
        assert isinstance(record["embedding"], list)
        assert isinstance(record["metadata"], dict)


@pytest.mark.skip(
    reason=(
        "environment-limited: requires Neo-APSU identity handshake and vector "
        "ingestion on hardware"
    )
)
def test_identity_contract_hardware_path_placeholder() -> None:
    """Placeholder for the hardware-backed identity handshake validation."""

    pytest.skip("Identity contract handshake requires Neo-APSU hardware replay.")
