from __future__ import annotations

"""Simple frequency-based steganography routines."""

from typing import Sequence

import numpy as np


DEFAULT_BASE_FREQ = 440.0
DEFAULT_DELTA_FREQ = 40.0
DEFAULT_BIT_DURATION = 0.05
DEFAULT_SAMPLE_RATE = 44100


def _generate_tone(
    frequency: float,
    duration: float,
    *,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> np.ndarray:
    """Return a normalized sine tone for ``duration`` seconds."""

    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    tone = 0.1 * np.sin(2 * np.pi * frequency * t)
    return tone.astype(np.float32)


def _bytes_to_bits(data: bytes) -> list[int]:
    bits: list[int] = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def encode_phrase(
    phrase: str,
    *,
    base_freq: float = DEFAULT_BASE_FREQ,
    delta_freq: float = DEFAULT_DELTA_FREQ,
    bit_duration: float = DEFAULT_BIT_DURATION,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> np.ndarray:
    """Encode ``phrase`` into a waveform using simple frequency keying."""

    msg_bytes = phrase.encode("utf-8")
    header = len(msg_bytes).to_bytes(2, "big")
    payload = header + msg_bytes
    bits = _bytes_to_bits(payload)

    tones: Sequence[np.ndarray] = []
    for bit in bits:
        freq = base_freq + delta_freq if bit else base_freq
        tone = _generate_tone(freq, bit_duration, sample_rate=sample_rate)
        tones.append(tone)

    if tones:
        waveform = np.concatenate(tones)
    else:
        waveform = np.array([], dtype=np.float32)
    return waveform.astype(np.float32)


def decode_waveform(
    waveform: np.ndarray,
    *,
    base_freq: float = DEFAULT_BASE_FREQ,
    delta_freq: float = DEFAULT_DELTA_FREQ,
    bit_duration: float = DEFAULT_BIT_DURATION,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> str:
    """Decode a waveform produced by :func:`encode_phrase`."""

    samples_per_bit = int(bit_duration * sample_rate)
    if samples_per_bit <= 0:
        raise ValueError("Invalid bit duration")

    total_bits = len(waveform) // samples_per_bit
    bits: list[int] = []
    freqs = np.fft.rfftfreq(samples_per_bit, 1 / sample_rate)
    idx_base = np.argmin(np.abs(freqs - base_freq))
    idx_delta = np.argmin(np.abs(freqs - (base_freq + delta_freq)))

    for i in range(total_bits):
        segment = waveform[i * samples_per_bit : (i + 1) * samples_per_bit]
        spectrum = np.abs(np.fft.rfft(segment))
        bit = int(spectrum[idx_delta] > spectrum[idx_base])
        bits.append(bit)

    if len(bits) < 16:
        return ""

    length = 0
    for b in bits[:16]:
        length = (length << 1) | b

    needed = 16 + length * 8
    if needed > len(bits):
        return ""

    msg_bits = bits[16:needed]
    bytes_out = bytearray()
    for i in range(length):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | msg_bits[i * 8 + j]
        bytes_out.append(byte)

    return bytes_out.decode("utf-8", errors="ignore")
