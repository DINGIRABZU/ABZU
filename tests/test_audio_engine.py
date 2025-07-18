import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import audio_engine


def test_play_sound_uses_pydub(monkeypatch, tmp_path):
    events = {}

    class DummySeg:
        def __init__(self, path):
            events['loaded'] = path

    def dummy_from_file(path):
        return DummySeg(path)

    class DummyPB:
        def wait_done(self):
            events['waited'] = True
        def stop(self):
            events['stopped'] = True

    def dummy_play(audio):
        events['played'] = audio
        return DummyPB()

    monkeypatch.setattr(audio_engine, 'AudioSegment', types.SimpleNamespace(from_file=dummy_from_file))
    monkeypatch.setattr(audio_engine, '_play_with_simpleaudio', dummy_play)

    audio_engine.play_sound(tmp_path / 'x.wav')

    assert events['loaded'] == tmp_path / 'x.wav'
    assert isinstance(events['played'], DummySeg)
    assert events['waited']


def test_stop_all_joins_threads(monkeypatch):
    calls = {'stopped': 0, 'joined': 0}

    class DummyPB:
        def stop(self):
            calls['stopped'] += 1

    class DummyThread:
        def join(self, timeout=None):
            calls['joined'] += 1

    audio_engine._playbacks = [DummyPB(), DummyPB()]
    audio_engine._loops = [DummyThread()]

    audio_engine.stop_all()

    assert calls['stopped'] == 2
    assert calls['joined'] == 1
    assert audio_engine._playbacks == []
    assert audio_engine._loops == []
