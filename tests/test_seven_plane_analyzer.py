import sys
from pathlib import Path
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from MUSIC_FOUNDATION.inanna_music_COMPOSER_ai import InannaMusicInterpreter
from MUSIC_FOUNDATION.seven_plane_analyzer import analyze_seven_planes


def test_seven_plane_analyzer_keys(tmp_path):
    sample_rate = 22050
    t = np.linspace(0, 1.0, sample_rate, endpoint=False)
    tone = 0.5 * np.sin(2 * np.pi * 440 * t)
    wav_path = tmp_path / "tone.wav"
    sf.write(wav_path, tone, sample_rate)

    engine = InannaMusicInterpreter(str(wav_path))
    engine.load_audio()
    engine.analyze()
    planes = engine.analyze_planes()

    expected = {
        "physical",
        "emotional",
        "mental",
        "astral",
        "etheric",
        "celestial",
        "divine",
    }
    assert set(planes.keys()) == expected


def test_analyze_seven_planes_mixed_waveform(tmp_path):
    """analyze_seven_planes should return all seven plane keys."""
    sr = 22050
    t = np.linspace(0, 1.0, sr, endpoint=False)
    mix = (
        0.5 * np.sin(2 * np.pi * 220 * t)
        + 0.25 * np.sin(2 * np.pi * 330 * t)
        + 0.1 * np.random.randn(sr)
    ).astype(np.float32)

    wav = tmp_path / "mix.wav"
    sf.write(wav, mix, sr)

    data, _ = sf.read(wav)
    planes = analyze_seven_planes(data, sr)

    expected = {
        "physical",
        "emotional",
        "mental",
        "astral",
        "etheric",
        "celestial",
        "divine",
    }
    assert set(planes.keys()) == expected
