from __future__ import annotations

from pathlib import Path

import pytest

import modulation_arrangement as ma
from src.audio import engine
from src.audio.telemetry import telemetry
from tests import conftest as conftest_module


conftest_module.ALLOWED_TESTS.add(str(Path(__file__).resolve()))


class DummySegment:
    """Minimal audio segment stand-in for telemetry tests."""

    def __init__(self, label: str = "") -> None:
        self.label = label

    @classmethod
    def from_file(cls, path: Path) -> "DummySegment":
        return cls(str(path))

    def apply_gain(self, _gain: float) -> "DummySegment":
        return self

    def pan(self, _pan: float) -> "DummySegment":
        return DummySegment(self.label + "|pan")

    def overlay(self, other: "DummySegment") -> "DummySegment":
        return DummySegment(self.label + "+" + other.label)

    def export(
        self, _path: Path, format: str = "wav", **_kwargs
    ) -> None:  # noqa: A002 - match AudioSegment signature
        return None


@pytest.fixture(autouse=True)
def clear_telemetry() -> None:
    telemetry.clear()


def test_layer_stems_emits_success_metric(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(ma, "AudioSegment", DummySegment)
    stems = {
        "left": tmp_path / "left.wav",
        "right": tmp_path / "right.wav",
    }
    ma.layer_stems(stems)
    events = telemetry.get_events()
    success = [
        event
        for event in events
        if event["event"] == "modulation.layer_stems" and event["status"] == "success"
    ]
    assert success, f"Expected success telemetry, got: {events}"
    assert success[-1]["stem_count"] == 2
    assert success[-1]["backend"] == "pydub"


def test_export_session_records_fallback(monkeypatch, tmp_path) -> None:
    segment = DummySegment("mix")

    def _raise(*_args, **_kwargs):
        raise ma.DAWUnavailableError(["ardour"], "install", {"ardour": False})

    monkeypatch.setattr(ma, "write_ardour_session", _raise)
    audio_path = tmp_path / "mix.wav"
    ma.export_session(segment, audio_path, session_format="ardour")
    events = telemetry.get_events()
    fallback = [
        event
        for event in events
        if event["event"] == "modulation.export_session"
        and event["status"] == "fallback"
    ]
    assert fallback, f"Expected fallback telemetry, got: {events}"
    assert fallback[-1]["session_format"] == "ardour"


def test_play_sound_failure_when_backend_missing(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(engine, "AudioSegment", None)
    path = tmp_path / "sample.wav"
    engine.play_sound(path)
    events = telemetry.get_events()
    failure = [
        event
        for event in events
        if event["event"] == "audio.play_sound" and event["status"] == "failure"
    ]
    assert failure, f"Expected failure telemetry, got: {events}"
    assert failure[-1]["reason"] == "audio_segment_unavailable"


def test_play_sound_success_records_metrics(monkeypatch, tmp_path) -> None:
    class _DummyPlayback:
        def wait_done(self) -> None:  # pragma: no cover - trivial
            return None

        def stop(self) -> None:  # pragma: no cover - trivial
            return None

    class _DummyAudio(DummySegment):
        pass

    def fake_play(seg):
        return _DummyPlayback()

    monkeypatch.setattr(engine, "AudioSegment", _DummyAudio)
    monkeypatch.setattr(engine, "_play_with_simpleaudio", fake_play)
    monkeypatch.setattr(engine, "_has_ffmpeg", lambda: True)
    path = tmp_path / "tone.wav"
    engine.play_sound(path)
    events = telemetry.get_events()
    assert any(
        e["event"] == "audio.play_segment" and e["status"] == "success" for e in events
    ), events
    assert any(
        e["event"] == "audio.play_sound" and e["status"] in {"completed", "started"}
        for e in events
    ), events
    engine._playbacks.clear()
