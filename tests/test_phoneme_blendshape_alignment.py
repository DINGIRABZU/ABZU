"""Integration tests for phoneme extraction and blendshape mapping."""

from __future__ import annotations

from ai_core.avatar.lip_sync import align_phonemes
from ai_core.avatar.phonemes import extract_phonemes
from ai_core.avatar.expression_controller import map_phonemes_to_blendshapes


def test_phoneme_blendshape_alignment_cycle():
    phonemes = extract_phonemes("mama")
    durations = [0.1] * len(phonemes)
    frame_map = align_phonemes(phonemes, durations, fps=10)
    blendshapes = map_phonemes_to_blendshapes([p for _, p in frame_map])
    assert blendshapes == ["closed", "open", "closed", "open"]

