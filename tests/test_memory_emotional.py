import memory_emotional as me
import pytest


def test_log_and_fetch(tmp_path):
    db_path = tmp_path / "emotions.db"
    e1 = me.log_emotion([0.1, 0.2], db_path=db_path)
    e2 = me.log_emotion([0.3, 0.4], db_path=db_path)
    history = me.fetch_emotion_history(10**6, db_path=db_path)
    assert [e.vector for e in history] == [e1.vector, e2.vector]


def test_env_var_db_path(tmp_path, monkeypatch):
    db_path = tmp_path / "emotions_env.db"
    monkeypatch.setenv("EMOTION_DB_PATH", str(db_path))
    entry = me.log_emotion([0.5, 0.6])
    history = me.fetch_emotion_history(10**6)
    assert history and history[0].vector == entry.vector


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
