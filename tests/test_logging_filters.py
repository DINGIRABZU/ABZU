from __future__ import annotations

import logging

import logging_filters


def test_emotion_filter_enriches_record():
    logging_filters.set_emotion_provider(lambda: ("joy", 0.75))
    record = logging.LogRecord("name", logging.INFO, "", 0, "msg", (), None)
    flt = logging_filters.EmotionFilter()
    assert flt.filter(record)
    assert record.emotion == "joy"
    assert record.resonance == 0.75


def test_emotion_filter_handles_runtime_failure(caplog):
    def boom():
        raise RuntimeError("boom")

    logging_filters.set_emotion_provider(boom)
    record = logging.LogRecord("name", logging.INFO, "", 0, "msg", (), None)
    with caplog.at_level(logging.WARNING):
        flt = logging_filters.EmotionFilter()
        assert flt.filter(record)
    assert record.emotion is None
    assert record.resonance is None
    assert "emotion provider runtime error" in caplog.text


def test_emotion_filter_handles_invalid_data(caplog):
    def not_a_tuple():
        return 123  # wrong return type

    logging_filters.set_emotion_provider(not_a_tuple)
    record = logging.LogRecord("name", logging.INFO, "", 0, "msg", (), None)
    with caplog.at_level(logging.WARNING):
        flt = logging_filters.EmotionFilter()
        assert flt.filter(record)
    assert record.emotion is None
    assert record.resonance is None
    assert "returned invalid data" in caplog.text

