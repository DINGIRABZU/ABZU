import memory_emotional as me
import pytest


def test_log_and_fetch(tmp_path):
    db_path = tmp_path / "emotions.db"
    conn = me.get_connection(db_path)
    try:
        e1 = me.log_emotion([0.1, 0.2], conn)
        e2 = me.log_emotion([0.3, 0.4], conn)
        history = me.fetch_emotion_history(10**6, conn)
        assert [e.vector for e in history] == [e1.vector, e2.vector]
    finally:
        conn.close()


def test_graceful_degradation_without_optional_dependencies(tmp_path, monkeypatch):
    monkeypatch.setattr(me, "AutoFeatureExtractor", None)
    monkeypatch.setattr(me, "dlib", None)
    conn = me.get_connection(tmp_path / "emotions.db")
    try:
        with pytest.raises(TypeError):
            me.log_emotion("not a sequence", conn)
        entry = me.log_emotion([1, 2], conn)
        assert entry.vector == [1.0, 2.0]
    finally:
        conn.close()
