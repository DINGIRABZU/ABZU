"""Tests for nazarick messaging."""

from agents.albedo import compose_message_nazarick
from albedo import State, Magnitude


def test_demiurge_message_high_trust():
    msg = compose_message_nazarick("Demiurge", State.CITRINITAS, Magnitude.EIGHT)
    expected = "Rank 2 Demiurge, continue operations with trust 8 and state citrinitas."
    assert msg == expected


def test_shalltear_message_low_trust():
    msg = compose_message_nazarick("Shalltear", State.NIGREDO, Magnitude.ZERO)
    expected = (
        "Rank 1 Shalltear, your loyalty is questioned at trust 0. Maintain nigredo."
    )
    assert msg == expected


def test_cocytus_message_mid_trust():
    msg = compose_message_nazarick("Cocytus", State.ALBEDO, Magnitude.FIVE)
    expected = "Rank 3 Cocytus, trust 5 maintains albedo."
    assert msg == expected
