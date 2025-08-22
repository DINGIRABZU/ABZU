from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from MUSIC_FOUNDATION.synthetic_stego_engine import decode_waveform, encode_phrase


def test_round_trip_encoding():
    phrase = "sacred fire"
    waveform = encode_phrase(phrase)
    assert isinstance(waveform, np.ndarray)
    decoded = decode_waveform(waveform)
    assert decoded == phrase
