"""
human_music_to_qnl_converter.py
INANNA_AI — QNL Music Transmutation Core

This module receives symbolic musical data (from MP3 analysis) and translates it into QNL code,
glosses, and optionally symbolic ritual audio frames.

Requires:
- Input: tempo, chroma (pitch class profile), duration
- Uses: glyph mappings, tone-frequency-emotion structures

Author: ZOHAR · Spiral Code Architect
"""

import json
import numpy as np

from .qnl_utils import chroma_to_qnl, generate_qnl_structure


def generate_qnl_song_structure(chroma_vector, tempo, metadata=None):
    """Backward compatible wrapper for ``generate_qnl_structure``."""
    return generate_qnl_structure(chroma_vector, tempo, metadata)

def export_qnl(json_data, output_path="output/qnl_song.json"):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    print(f"✅ QNL structure saved to: {output_path}")

if __name__ == "__main__":
    # Test QNL conversion (example)
    dummy_chroma = np.array([0.1, 0.05, 0.3, 0.15, 0.2, 0.1, 0.05, 0.6, 0.4, 0.2, 0.1, 0.05])
    tempo = 92.0

    result = generate_qnl_song_structure(dummy_chroma, tempo, metadata={"title": "Test Song"})
    export_qnl(result, output_path="output/qnl_test_song.json")
