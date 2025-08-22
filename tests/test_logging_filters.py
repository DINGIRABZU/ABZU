from __future__ import annotations

import logging

import pytest

import logging_filters


def test_emotion_filter_logs_when_registry_fails(monkeypatch, caplog):
    class DummyRegistry:
        def get_last_emotion(self):
            raise RuntimeError("boom")

        def get_resonance_level(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(logging_filters, "emotion_registry", DummyRegistry())
    with caplog.at_level(logging.WARNING):
        record = logging.LogRecord("name", logging.INFO, "", 0, "msg", (), None)
        flt = logging_filters.EmotionFilter()
        assert flt.filter(record)
    assert record.emotion is None
    assert record.resonance is None
    assert "emotion_registry fetch failed" in caplog.text


def test_emotion_filter_logs_when_state_fails(monkeypatch, caplog):
    class DummyState:
        def get_last_emotion(self):
            raise RuntimeError("boom")

        def get_resonance_level(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(logging_filters, "emotion_registry", None)
    monkeypatch.setattr(logging_filters, "emotional_state", DummyState(), raising=False)
    with caplog.at_level(logging.WARNING):
        record = logging.LogRecord("name", logging.INFO, "", 0, "msg", (), None)
        flt = logging_filters.EmotionFilter()
        assert flt.filter(record)
    assert record.emotion is None
    assert record.resonance is None
    assert "emotional_state fetch failed" in caplog.text
