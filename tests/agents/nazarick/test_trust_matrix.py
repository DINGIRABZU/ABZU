"""Tests for trust matrix."""

from __future__ import annotations

from agents.nazarick.trust_matrix import EntityType, TrustMatrix


def test_classify_entities(tmp_path):
    db = tmp_path / "trust.db"
    tm = TrustMatrix(db)

    etype, rank = tm.classify("Shalltear")
    assert etype is EntityType.NAZARICK
    assert rank == 1

    etype, rank = tm.classify("Empire")
    assert etype is EntityType.RIVAL
    assert rank == 3

    etype, rank = tm.classify("Bob")
    assert etype is EntityType.OUTSIDER
    assert rank is None


def test_protocol_lookup(tmp_path):
    db = tmp_path / "trust.db"
    tm = TrustMatrix(db)

    tm.set_trust("Demiurge", 9)
    assert tm.lookup_protocol("Demiurge") == "nazarick_rank2_high"

    tm.set_trust("Slane", 2)
    assert tm.lookup_protocol("Slane") == "rival_level2_wrath"
