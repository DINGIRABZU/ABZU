"""Identity contract placeholder validations.

Entry point:
    pytest tests/contracts/test_identity_contract.py

Anchored to ``docs/contracts/identity.md`` and the ``identity_loader.py``
row in ``docs/apsu_migration_matrix.md``. TODO hardware replay once the
Neo-APSU identity bindings stream telemetry from the hardware runner.
"""

from __future__ import annotations

import pytest

from .utils import HARDWARE_TODO_NOTE, load_contract_fixture


def test_identity_vector_fixture_shape() -> None:
    """Check the vector baseline used by identity ingestion."""

    payload = load_contract_fixture("chroma_baseline", "baseline.json")
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
        "ingestion on hardware; " + HARDWARE_TODO_NOTE
    )
)
def test_identity_contract_hardware_path_placeholder() -> None:
    """Placeholder for the hardware-backed identity handshake validation."""

    pytest.skip(
        "TODO hardware replay: identity handshake requires Neo-APSU hardware replay."
    )
