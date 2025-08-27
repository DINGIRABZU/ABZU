"""Tests for Nazarick persona profile loader."""

from agents.nazarick import load_persona_profiles


def test_load_persona_profiles_returns_expected_entries():
    profiles = load_persona_profiles()
    assert profiles["demiurge"]["floor"] == 7
    assert profiles["shalltear"]["channel"] == "Catacombs"
