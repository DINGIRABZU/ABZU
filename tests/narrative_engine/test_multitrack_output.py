"""Tests for multitrack output."""

from memory.narrative_engine import StoryEvent, compose_multitrack_story

from core import expressive_output

__version__ = "0.1.0"


def test_tracks_present():
    events = [StoryEvent(actor="Hero", action="draws sword")]
    result = compose_multitrack_story(events)
    assert set(result) == {"prose", "audio", "visual", "usd"}
    assert isinstance(result["prose"], str) and result["prose"]
    for key in ("audio", "visual", "usd"):
        assert isinstance(result[key], list)
        assert result[key]


def test_streaming_invokes_expressive_output(monkeypatch):
    events = [StoryEvent(actor="Hero", action="speaks")]

    called: dict[str, object] = {}

    def fake_speak(text: str, emotion: str):
        called["text"] = text
        called["emotion"] = emotion

    def fake_set_cb(cb):
        called["cb"] = cb

    monkeypatch.setattr(expressive_output, "speak", fake_speak)
    monkeypatch.setattr(expressive_output, "set_frame_callback", fake_set_cb)

    cb = lambda f: None
    compose_multitrack_story(events, stream=True, emotion="calm", frame_callback=cb)

    assert called["text"] == "Hero speaks."
    assert called["emotion"] == "calm"
    assert called["cb"] is cb
