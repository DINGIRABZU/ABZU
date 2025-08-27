from __future__ import annotations

from agents.nazarick.ethics_manifesto import Manifesto, LAWS


def test_get_law_returns_expected_law():
    manifesto = Manifesto()
    first_name = LAWS[0].name
    law = manifesto.get_law(first_name)
    assert law == LAWS[0]


def test_validate_action_flags_keywords():
    manifesto = Manifesto()
    result = manifesto.validate_action("Ainz", "prepare to attack the village")
    assert not result["compliant"]
    assert LAWS[0].name in result["violated_laws"]

    clean = manifesto.validate_action("Albedo", "offer aid to villagers")
    assert clean["compliant"]
    assert clean["violated_laws"] == []
