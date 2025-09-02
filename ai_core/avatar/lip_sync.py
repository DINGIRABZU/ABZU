"""Utilities for aligning phonemes with video frame indices."""

from __future__ import annotations

from typing import List, Sequence, Tuple

FramePhoneme = Tuple[int, str]


def align_phonemes(
    phonemes: Sequence[str], durations: Sequence[float], fps: int
) -> List[FramePhoneme]:
    """Map ``phonemes`` to frame indices based on ``durations``.

    Parameters
    ----------
    phonemes:
        Ordered collection of phoneme symbols.
    durations:
        Duration of each phoneme in seconds.  Must match ``phonemes`` in
        length.
    fps:
        Frames per second of the target video.

    Returns
    -------
    List[Tuple[int, str]]
        Sequence where each tuple contains the frame index and the phoneme that
        should be displayed.  The last frame index is ``len(result) - 1``.
    """

    if len(phonemes) != len(durations):  # pragma: no cover - defensive
        raise ValueError("phonemes and durations must be the same length")

    frame_map: List[FramePhoneme] = []
    frame_index = 0
    for phoneme, dur in zip(phonemes, durations):
        count = max(1, int(round(dur * fps)))
        for _ in range(count):
            frame_map.append((frame_index, phoneme))
            frame_index += 1
    return frame_map


__all__ = ["align_phonemes", "FramePhoneme"]
