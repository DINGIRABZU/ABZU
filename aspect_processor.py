from __future__ import annotations

"""Utility functions for aspect analysis and logging.

This module provides simple analysis helpers that log results under
``data/aspects``. Each analyser returns a dictionary of metrics while
appending the same information to an aspect-specific log file for
auditing and cross-layer referencing.
"""

from datetime import datetime
from pathlib import Path
import json
from typing import Any, Dict

ASPECT_LOG_DIR = Path(__file__).resolve().parent / "data" / "aspects"
ASPECT_LOG_DIR.mkdir(parents=True, exist_ok=True)


def _log(aspect: str, data: Dict[str, Any]) -> None:
    """Append ``data`` to the log file for ``aspect``."""

    log_path = ASPECT_LOG_DIR / f"{aspect}.log"
    entry = {"timestamp": datetime.utcnow().isoformat(), **data}
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False))
        fh.write("\n")


def analyze_phonetic(text: str) -> Dict[str, Any]:
    """Perform a basic phonetic analysis of ``text`` and log the result."""

    vowels = sum(c.lower() in "aeiou" for c in text)
    analysis = {"text": text, "vowel_count": vowels, "length": len(text)}
    _log("phonetic", analysis)
    return analysis


def analyze_semantic(text: str) -> Dict[str, Any]:
    """Perform a rudimentary semantic analysis of ``text`` and log it."""

    tokens = text.split()
    analysis = {
        "text": text,
        "token_count": len(tokens),
        "unique_tokens": len(set(tokens)),
    }
    _log("semantic", analysis)
    return analysis


__all__ = ["analyze_phonetic", "analyze_semantic", "ASPECT_LOG_DIR"]
