from albedo import Magnitude, State
from albedo.state_machine import AlbedoStateMachine, EntityCategory


def test_zero_trust_resets_state():
    machine = AlbedoStateMachine()
    machine.state = State.RUBEDO
    assert machine.transition(Magnitude.ZERO, EntityCategory.ALLY) is State.NIGREDO


def test_max_trust_ally_reaches_rubedo():
    machine = AlbedoStateMachine()
    assert machine.transition(Magnitude.TEN, EntityCategory.ALLY) is State.RUBEDO


def test_max_trust_neutral_stops_at_citrinitas():
    machine = AlbedoStateMachine()
    assert machine.transition(Magnitude.TEN, EntityCategory.NEUTRAL) is State.CITRINITAS
