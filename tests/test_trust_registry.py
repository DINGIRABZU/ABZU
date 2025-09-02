"""Tests for trust registry."""

from __future__ import annotations

import json

from memory import trust_registry


def test_entity_detection_and_persistence(tmp_path, monkeypatch):
    registry = tmp_path / "trust_registry.json"
    monkeypatch.setattr(trust_registry, "TRUST_REGISTRY", registry)

    # Known Nazarick role
    category, trust = trust_registry.detect_entity("Albedo")
    assert category == "nazarick"
    assert trust == trust_registry.NAZARICK_ROLES["albedo"]

    # Rival entity
    category, trust = trust_registry.detect_entity("Clementine")
    assert category == "rival"
    assert trust == trust_registry.RIVALS["clementine"]

    # Outsider
    category, trust = trust_registry.detect_entity("Bob")
    assert category == "outsider"
    assert trust == trust_registry.DEFAULT_OUTSIDER_TRUST

    # Invoke again to confirm history persistence
    trust_registry.detect_entity("Albedo")
    data = json.loads(registry.read_text())
    assert data["albedo"] == [
        trust_registry.NAZARICK_ROLES["albedo"],
        trust_registry.NAZARICK_ROLES["albedo"],
    ]
    assert data["clementine"] == [trust_registry.RIVALS["clementine"]]
    assert data["bob"] == [trust_registry.DEFAULT_OUTSIDER_TRUST]
