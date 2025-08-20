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


def test_without_optional_dependencies(tmp_path, monkeypatch):
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


def test_huggingface_extractor(tmp_path, monkeypatch):
    class DummyExtractor:
        @classmethod
        def from_pretrained(cls, name):
            return cls()

        def __call__(self, data):
            return [0, 1, 2]

    monkeypatch.setattr(me, "AutoFeatureExtractor", DummyExtractor)
    conn = me.get_connection(tmp_path / "emotions.db")
    try:
        entry = me.log_emotion("raw data", conn)
        assert entry.vector == [0.0, 1.0, 2.0]
    finally:
        conn.close()


def test_dlib_extractor(tmp_path, monkeypatch):
    class DummyDlib:
        @staticmethod
        def vector(data):
            return [3, 4]

    monkeypatch.setattr(me, "AutoFeatureExtractor", None)
    monkeypatch.setattr(me, "dlib", DummyDlib)
    conn = me.get_connection(tmp_path / "emotions.db")
    try:
        entry = me.log_emotion("raw data", conn)
        assert entry.vector == [3.0, 4.0]
    finally:
        conn.close()
