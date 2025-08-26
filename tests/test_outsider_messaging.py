from agents.albedo import compose_message_outsider
from albedo import State, Magnitude


def test_recruit_diplomatic():
    msg = compose_message_outsider("Scout", State.ALBEDO, Magnitude.NINE)
    expected = "Recruit Scout, diplomacy thrives at trust 9 in albedo."
    assert msg == expected


def test_neutral_analytic():
    msg = compose_message_outsider("Merchant", State.CITRINITAS, Magnitude.FIVE)
    expected = "Neutral Merchant, review shows citrinitas at trust 5."
    assert msg == expected


def test_suspect_warning():
    msg = compose_message_outsider("Spy", State.RUBEDO, Magnitude.TWO)
    expected = "Suspect Spy, threat detected at trust 2; rubedo compromised."
    assert msg == expected


def test_dangerous_warning():
    msg = compose_message_outsider("Raider", State.NIGREDO, Magnitude.ONE)
    expected = "Dangerous Raider, imminent danger with trust 1; nigredo failing."
    assert msg == expected
