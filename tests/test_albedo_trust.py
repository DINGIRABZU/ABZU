import json

from agents.albedo import trust
from albedo import Magnitude, State
from src.core.utils.seed import seed_all


def test_trust_promotion(tmp_path, monkeypatch):
    log = tmp_path / "albedo_interactions.jsonl"
    monkeypatch.setattr(trust, "LOG_FILE", log)
    monkeypatch.setattr(trust, "TRUST_SCORES", {})

    mag, state = trust.update_trust("Bob", "positive")
    assert mag == Magnitude.SIX
    assert state == State.CITRINITAS

    mag2, state2 = trust.update_trust("Bob", "positive")
    assert mag2 == Magnitude.SEVEN
    assert state2 == State.CITRINITAS

    entry = json.loads(log.read_text().splitlines()[-1])
    assert entry["magnitude"] == 7
    assert entry["state"] == "citrinitas"


def test_trust_decay(tmp_path, monkeypatch):
    log = tmp_path / "albedo_interactions.jsonl"
    monkeypatch.setattr(trust, "LOG_FILE", log)
    monkeypatch.setattr(trust, "TRUST_SCORES", {})

    mag1, state1 = trust.update_trust("Bob", "negative")
    assert mag1 == Magnitude.FOUR
    assert state1 == State.ALBEDO

    mag2, state2 = trust.update_trust("Bob", "negative")
    assert mag2 == Magnitude.THREE
    assert state2 == State.ALBEDO

    mag3, state3 = trust.update_trust("Bob", "negative")
    assert mag3 == Magnitude.TWO
    assert state3 == State.NIGREDO

    entry = json.loads(log.read_text().splitlines()[-1])
    assert entry["magnitude"] == 2
    assert entry["state"] == "nigredo"


def test_seed_all_executes():
    seed_all(123)
