import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI import silence_reflection


def test_is_sustained_silence():
    wave = np.zeros(44100 * 2, dtype=np.float32)
    assert silence_reflection.is_sustained_silence(wave, 44100)

    short_wave = np.zeros(22050, dtype=np.float32)
    assert not silence_reflection.is_sustained_silence(short_wave, 44100)


def test_silence_meaning():
    long_wave = np.zeros(44100 * 2, dtype=np.float32)
    assert "Extended" in silence_reflection.silence_meaning(long_wave, 44100)

    short_wave = np.zeros(22050, dtype=np.float32)
    assert "Brief" in silence_reflection.silence_meaning(short_wave, 44100)
