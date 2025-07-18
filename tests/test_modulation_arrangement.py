import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import modulation_arrangement as ma


class DummySeg:
    def __init__(self, name="seg"):
        self.name = name
        self.pan_val = None
        self.gain_val = None
        self.slice = None
        self.fade_in_ms = None
        self.fade_out_ms = None

    def pan(self, val):
        self.pan_val = val
        return self

    def overlay(self, other):
        return DummySeg(f"{self.name}+{other.name}")

    def apply_gain(self, val):
        self.gain_val = val
        return self

    def __getitem__(self, item):
        self.slice = item
        return self

    def fade_in(self, ms):
        self.fade_in_ms = ms
        return self

    def fade_out(self, ms):
        self.fade_out_ms = ms
        return self

    def export(self, path, format="wav"):
        events.append(("export", path, format))


class DummyAudioModule:
    def __init__(self):
        self.from_file_calls = []
        self.objects = []

    def from_file(self, path):
        self.from_file_calls.append(path)
        obj = DummySeg(Path(path).stem)
        self.objects.append(obj)
        return obj


def test_layer_stems(monkeypatch):
    audio = DummyAudioModule()
    monkeypatch.setattr(ma, "AudioSegment", audio)

    stems = {"vocals": Path("vocals.wav"), "drums": Path("drums.wav")}
    mix = ma.layer_stems(stems, pans=[-1, 1], volumes=[-3, -6])

    assert audio.from_file_calls == [Path("vocals.wav"), Path("drums.wav")]
    assert isinstance(mix, DummySeg)
    assert [obj.pan_val for obj in audio.objects] == [-1, 1]
    assert [obj.gain_val for obj in audio.objects] == [-3, -6]


def test_slice_and_fade(monkeypatch):
    seg = DummySeg()
    events.clear()
    out = ma.slice_loop(seg, 0.5, 1.0)
    assert seg.slice == slice(500, 1500)
    monkeypatch.setattr(ma, "AudioSegment", types.SimpleNamespace())
    faded = ma.apply_fades(seg, 100, 200)
    assert faded.fade_in_ms == 100
    assert faded.fade_out_ms == 200


def test_export_mix(monkeypatch, tmp_path):
    seg = DummySeg()
    events.clear()
    ma.export_mix(seg, tmp_path / "x.wav")
    assert events == [("export", tmp_path / "x.wav", "wav")]


def test_session_writers(monkeypatch, tmp_path):
    monkeypatch.setattr(ma.shutil, "which", lambda x: True)
    ardour = ma.write_ardour_session(Path("mix.wav"), tmp_path / "a.ardour")
    assert ardour.read_text().startswith("<Session>")
    carla = ma.write_carla_project(Path("mix.wav"), tmp_path / "c.carxs")
    assert "CarlaPatchbay" in carla.read_text()


def test_export_session(monkeypatch, tmp_path):
    def stub_ardour(a, b):
        b.write_text("a")
        return b

    def stub_carla(a, b):
        b.write_text("c")
        return b

    monkeypatch.setattr(ma, "write_ardour_session", stub_ardour)
    monkeypatch.setattr(ma, "write_carla_project", stub_carla)
    seg = DummySeg()
    events.clear()
    out = ma.export_session(seg, tmp_path / "mix.wav", session_format="carla")
    assert events == [("export", tmp_path / "mix.wav", "wav")]
    assert out.read_text() == "c"


events = []
