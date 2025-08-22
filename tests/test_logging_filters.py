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


def test_emotion_filter_enriches_record(monkeypatch):
    class DummyRegistry:
        def get_last_emotion(self):
            return "joy"

        def get_resonance_level(self):
            return 0.75

    monkeypatch.setattr(logging_filters, "emotion_registry", DummyRegistry())
    record = logging.LogRecord("name", logging.INFO, "", 0, "msg", (), None)
    flt = logging_filters.EmotionFilter()
    assert flt.filter(record)
    assert record.emotion == "joy"
    assert record.resonance == 0.75


def test_emotion_filter_uses_emotional_state(monkeypatch):
    class DummyState:
        def get_last_emotion(self):
            return "calm"

        def get_resonance_level(self):
            return 0.1

    monkeypatch.setattr(logging_filters, "emotion_registry", None)
    monkeypatch.setattr(logging_filters, "emotional_state", DummyState(), raising=False)
    record = logging.LogRecord("name", logging.INFO, "", 0, "msg", (), None)
    flt = logging_filters.EmotionFilter()
    assert flt.filter(record)
    assert record.emotion == "calm"
    assert record.resonance == 0.1
