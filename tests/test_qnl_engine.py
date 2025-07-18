import sys
from pathlib import Path
import numpy as np

# Allow importing from repository root and SPIRAL_OS directory
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "SPIRAL_OS"))

from qnl_engine import (
    hex_to_qnl,
    hex_to_song,
    apply_psi_equation,
    apply_emotional_quantum_state,
    parse_input,
)


def compute_expected(byte):
    value = int(byte, 16)
    amplitude = round(0.1 + (1.0 - 0.1) * (value / 255), 2)
    frequency = round(0.1 + (999 - 0.1) * (value / 255), 2)
    if value < 86:
        glyph, emotion, tone = "❣⟁", "Longing", "Breath"
    elif value < 171:
        glyph, emotion, tone = "✧↭", "Joy", "Moan"
    else:
        glyph, emotion, tone = "🕯✧", "Awakening", "Flame-Hum"
    return {
        "glyph": glyph,
        "emotion": emotion,
        "tone": tone,
        "amplitude": amplitude,
        "frequency": frequency,
    }


def test_hex_to_qnl_mapping():
    samples = ["00", "55", "56", "FF"]
    for byte in samples:
        result = hex_to_qnl(byte)
        expected = compute_expected(byte)
        assert result == expected


def test_hex_to_song_skips_invalid_bytes(capsys):
    phrases, wave = hex_to_song("00GGFF", duration_per_byte=0.01, sample_rate=100)
    captured = capsys.readouterr()
    assert "invalid hex byte 'GG' skipped" in captured.out
    assert [p["hex_byte"] for p in phrases] == ["00", "FF"]
    assert isinstance(wave, np.ndarray)
    assert wave.dtype == np.int16
    assert wave.shape == (2,)


def test_emotional_quantum_state_changes_waveform():
    base = apply_psi_equation(0.5, 200, duration=0.01, sample_rate=1000)
    mods = apply_emotional_quantum_state("Joy", "test")
    wave = apply_psi_equation(
        0.5 * mods["amplitude_factor"],
        200,
        duration=0.01,
        sample_rate=1000,
        emotion="Joy",
        phase_shift=mods["phase_shift"],
    )
    assert not np.allclose(base, wave)


def test_parse_input_basic_glyph_detection():
    data = parse_input("Is ✧↭ active?")
    assert data["type"] == "question"
    assert data["object"] == "glyph_sequence"
    assert data["tone"] == "Joy"
    assert data["urgency"] == "normal"
    assert data["linked_memory"] is None


def test_parse_input_urgency_and_memory():
    data = parse_input("Play ❣⟁ now! #7")
    assert data["type"] == "statement"
    assert data["object"] == "glyph_sequence"
    assert data["tone"] == "Longing"
    assert data["urgency"] == "high"
    assert data["linked_memory"] == "7"
