from agents.albedo import compose_message_rival
from albedo import State, Magnitude
from src.core.utils.seed import seed_all


def test_clementine_teaching_mid_trust():
    msg = compose_message_rival("Clementine", State.CITRINITAS, Magnitude.SIX)
    expected = "Level 1 Clementine, at trust 6, learn the ways of citrinitas."
    assert msg == expected


def test_slane_wrath_low_trust():
    msg = compose_message_rival("Slane", State.NIGREDO, Magnitude.TWO)
    expected = "Level 2 Slane, trust 2 triggers nigredo wrath."
    assert msg == expected


def test_empire_teaching_high_trust():
    msg = compose_message_rival("Empire", State.CITRINITAS, Magnitude.TEN)
    expected = "Level 3 Empire, trust 10 reveals all citrinitas teachings."
    assert msg == expected


def test_kingdom_wrath_mid_trust():
    msg = compose_message_rival("Kingdom", State.NIGREDO, Magnitude.SEVEN)
    expected = "Level 4 Kingdom, with trust 7, nigredo scourges persist."
    assert msg == expected


def test_seed_all_executes():
    """Ensure seeding utility executes for coverage."""
    seed_all(0)
