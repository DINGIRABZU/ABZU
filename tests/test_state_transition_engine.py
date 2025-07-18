from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from state_transition_engine import StateTransitionEngine


def test_state_transitions():
    ste = StateTransitionEngine()
    assert ste.current_state() == "dormant"
    ste.update_state("I feel joy today")
    assert ste.current_state() == "active"
    ste.update_state("begin the ritual now")
    assert ste.current_state() == "ritual"
