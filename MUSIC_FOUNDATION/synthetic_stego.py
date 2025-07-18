"""Simple LSB audio steganography utilities."""

from __future__ import annotations

from typing import Tuple

import numpy as np
import soundfile as sf


def _to_int16(data: np.ndarray) -> np.ndarray:
    """Ensure waveform is 16-bit integer."""
    if data.dtype == np.int16:
        return data.copy()
    return np.clip(data * 32767, -32768, 32767).astype(np.int16)


def embed_data(input_wav: str, output_wav: str, message: str) -> None:
    """Embed ``message`` inside ``input_wav`` and write to ``output_wav``."""
    data, sr = sf.read(input_wav, always_2d=False)
    samples = _to_int16(data)

    msg_bytes = message.encode("utf-8")
    length = len(msg_bytes)
    header = length.to_bytes(4, "big")
    payload = header + msg_bytes

    bits = []
    for byte in payload:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)

    if len(bits) > samples.size:
        raise ValueError("Message too large for audio file")

    flat = samples.reshape(-1)
    for i, bit in enumerate(bits):
        flat[i] = (flat[i] & ~1) | bit
    samples = flat.reshape(samples.shape)

    sf.write(output_wav, samples, sr, subtype="PCM_16")


def extract_data(wav_path: str) -> str:
    """Extract a hidden message from ``wav_path``."""
    data, _ = sf.read(wav_path, always_2d=False, dtype="int16")
    flat = data.reshape(-1)
    bits = [int(sample & 1) for sample in flat]

    length = 0
    for b in bits[:32]:
        length = (length << 1) | b

    needed = 32 + length * 8
    if needed > len(bits):
        raise ValueError("Incomplete hidden message")

    msg_bits = bits[32:needed]
    bytes_out = bytearray()
    for i in range(length):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | msg_bits[i * 8 + j]
        bytes_out.append(byte)

    return bytes_out.decode("utf-8", errors="ignore")
