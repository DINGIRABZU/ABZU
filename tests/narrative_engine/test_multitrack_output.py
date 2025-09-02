"""Tests for multitrack output."""

from memory.narrative_engine import StoryEvent, compose_multitrack_story

__version__ = "0.1.0"


def test_tracks_present():
    events = [StoryEvent(actor="Hero", action="draws sword")]
    result = compose_multitrack_story(events)
    assert set(result) == {"prose", "audio", "visual", "usd"}
    assert isinstance(result["prose"], str) and result["prose"]
    for key in ("audio", "visual", "usd"):
        assert isinstance(result[key], list)
        assert result[key]
