"""Phoneme extraction utilities."""

from __future__ import annotations

from typing import List

from phonemizer import phonemize
from phonemizer.separator import Separator


def extract_phonemes(text: str, lang: str = "en-us") -> List[str]:
    """Return IPA phonemes for ``text``.

    The function uses :mod:`phonemizer` with the ``espeak`` backend and
    separates phonemes with spaces.  Word boundaries are ignored which keeps the
    result easy to align with audio frames.
    """

    separator = Separator(phone=" ", word="|")
    phoneme_str = phonemize(text, language=lang, separator=separator, strip=True)
    return [p for p in phoneme_str.split() if p and p != "|"]


__all__ = ["extract_phonemes"]

