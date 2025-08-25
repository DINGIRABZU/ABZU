"""Tests for play ritual music."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import logging

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("EmotiVoice", types.ModuleType("EmotiVoice"))
sys.modules.setdefault("gtts", types.ModuleType("gtts"))
sys.modules.setdefault("openvoice", types.ModuleType("openvoice"))
sys.modules.setdefault("sounddevice", types.ModuleType("sounddevice"))

import audio.play_ritual_music as prm


def test_play_ritual_music_cli(tmp_path, monkeypatch):
    def dummy_compose(
        tempo, melody, *, sample_rate=44100, wav_path=None, wave_type="sine"
    ):
        wave = np.zeros(100, dtype=np.float32)
        if wav_path:
            prm.backends._write_wav(Path(wav_path), wave, sample_rate)
        return wave

    monkeypatch.setattr(
        prm.waveform.layer_generators, "compose_human_layer", dummy_compose
    )
    monkeypatch.setattr(prm.backends, "sf", None)
    monkeypatch.setattr(prm.backends, "sa", None)
    monkeypatch.setattr(prm.waveform, "sf", object())

    out = tmp_path / "ritual.wav"
    prm.main(["--emotion", "joy", "--ritual", "\u2609", "--output", str(out)])

    assert out.exists()


def test_play_ritual_music_fallback(tmp_path, monkeypatch):
    def dummy_compose(
        tempo, melody, *, sample_rate=44100, wav_path=None, wave_type="sine"
    ):
        return np.zeros(100, dtype=np.float32)

    monkeypatch.setattr(
        prm.waveform.layer_generators, "compose_human_layer", dummy_compose
    )
    monkeypatch.setattr(prm.backends, "sf", None)
    monkeypatch.setattr(prm.backends, "sa", None)
    monkeypatch.setattr(prm.waveform, "sf", object())

    out = prm.compose_ritual_music(
        "joy", "\u2609", output_dir=tmp_path, sample_rate=8000
    )

    assert out.path.exists()
    assert out.path == tmp_path / "ritual.wav"
    assert out.sample_rate == 8000


def test_synthesize_melody_without_sf(tmp_path, monkeypatch):
    """Ensure internal synthesis is used when ``soundfile`` is missing."""

    # Avoid using external resolution logic
    monkeypatch.setattr(
        prm.emotion_params, "resolve", lambda *a, **k: (120.0, ["C4"], "sine", "albedo")
    )

    # Simulate missing soundfile in both modules
    monkeypatch.setattr(prm.backends, "sf", None)
    monkeypatch.setattr(prm.backends, "sa", None)
    monkeypatch.setattr(prm.waveform, "sf", None)

    called: dict[str, bool] = {}

    def dummy_synth(tempo, melody, *, wave_type="sine", sample_rate=44100):
        called["used"] = True
        return np.zeros(100, dtype=np.float32)

    monkeypatch.setattr(prm, "_synthesize_numpy", dummy_synth)

    def fail_compose(*args, **kwargs):  # pragma: no cover - should not run
        raise AssertionError("compose_human_layer should not be called")

    monkeypatch.setattr(
        prm.waveform.layer_generators, "compose_human_layer", fail_compose
    )

    out = prm.compose_ritual_music("joy", "\u2609", output_dir=tmp_path)

    assert out.path.exists()
    assert called["used"]


def test_synthesize_melody_with_sf(tmp_path, monkeypatch):
    """Ensure standard synthesis path is used when ``soundfile`` is present."""

    monkeypatch.setattr(
        prm.emotion_params, "resolve", lambda *a, **k: (120.0, ["C4"], "sine", "albedo")
    )

    called: dict[str, bool] = {}

    def dummy_compose(
        tempo, melody, *, sample_rate=44100, wav_path=None, wave_type="sine"
    ):
        called["used"] = True
        return np.zeros(100, dtype=np.float32)

    monkeypatch.setattr(
        prm.waveform.layer_generators, "compose_human_layer", dummy_compose
    )
    monkeypatch.setattr(prm.backends, "sf", None)
    monkeypatch.setattr(prm.backends, "sa", None)
    monkeypatch.setattr(prm.waveform, "sf", object())

    out = prm.compose_ritual_music("joy", "\u2609", output_dir=tmp_path)

    assert out.path.exists()
    assert called["used"]


def test_archetype_mix_fallback(monkeypatch, caplog):
    """Ensure NumPy tone is used when soundfile is missing."""

    monkeypatch.setattr(prm.backends, "sf", None)

    with caplog.at_level(logging.WARNING):
        mix = prm._get_archetype_mix("albedo", sample_rate=8000)

    assert mix.size > 0
    assert "soundfile not available" in caplog.text


def test_archetype_mix_soundfile_present(monkeypatch):
    """Verify overlay is decoded with soundfile when available."""

    called: dict[str, bool] = {}

    def fake_read(buf, dtype="float32"):
        called["used"] = True
        return np.zeros(10, dtype=np.float32), 44100

    fake_sf = types.SimpleNamespace(read=fake_read)
    monkeypatch.setattr(prm.backends, "sf", fake_sf)
    prm._get_archetype_mix.cache_clear()

    mix = prm._get_archetype_mix("albedo")

    assert called["used"]
    assert mix.shape[0] == 10


def test_encode_phrase_increases_size(tmp_path, monkeypatch):
    """Embedding a phrase should grow the output file size."""

    monkeypatch.setattr(
        prm.emotion_params, "resolve", lambda *a, **k: (120.0, ["C4"], "sine", "albedo")
    )
    monkeypatch.setattr(prm.backends, "sf", None)
    monkeypatch.setattr(prm.backends, "sa", None)
    monkeypatch.setattr(prm.waveform, "sf", object())

    def dummy_compose(
        tempo, melody, *, sample_rate=44100, wav_path=None, wave_type="sine"
    ):
        return np.zeros(100, dtype=np.float32)

    monkeypatch.setattr(
        prm.waveform.layer_generators, "compose_human_layer", dummy_compose
    )

    calls = {"count": 0}

    def fake_encode_phrase(phrase):
        calls["count"] += 1
        return np.ones(200, dtype=np.float32)

    monkeypatch.setattr(prm.stego, "encode_phrase", fake_encode_phrase)

    def fake_embed_phrase(wave, ritual, emotion):
        stego = prm.stego.encode_phrase("secret")
        return np.concatenate([wave, stego])

    monkeypatch.setattr(prm.stego, "embed_phrase", fake_embed_phrase)

    plain_dir = tmp_path / "plain"
    hidden_dir = tmp_path / "hidden"
    plain_dir.mkdir()
    hidden_dir.mkdir()

    out_plain = prm.compose_ritual_music("joy", "\u2609", output_dir=plain_dir)
    out_hidden = prm.compose_ritual_music(
        "joy", "\u2609", output_dir=hidden_dir, hide=True
    )

    assert calls["count"] == 1
    assert out_hidden.path.stat().st_size > out_plain.path.stat().st_size


def test_emotion_map_cached(tmp_path, monkeypatch):
    """Repeated calls should load mapping only once."""

    calls = {"count": 0}

    def fake_load(path):
        calls["count"] += 1
        return {}

    def fake_resolve(emotion, archetype=None):
        prm.emotion_params.load_emotion_music_map(prm.emotion_params.EMOTION_MAP)
        return 120.0, ["C4"], "sine", "albedo"

    monkeypatch.setattr(prm.emotion_params, "load_emotion_music_map", fake_load)
    monkeypatch.setattr(prm.emotion_params, "resolve", fake_resolve)

    def dummy_compose(
        tempo, melody, *, sample_rate=44100, wav_path=None, wave_type="sine"
    ):
        return np.zeros(100, dtype=np.float32)

    monkeypatch.setattr(
        prm.waveform.layer_generators, "compose_human_layer", dummy_compose
    )
    monkeypatch.setattr(prm.backends, "sf", None)
    monkeypatch.setattr(prm.backends, "sa", None)
    monkeypatch.setattr(prm.waveform, "sf", object())

    prm.map_emotion.cache_clear()
    prm.compose_ritual_music("joy", "\u2609", output_dir=tmp_path)
    prm.compose_ritual_music("joy", "\u2609", output_dir=tmp_path)

    assert calls["count"] == 1
