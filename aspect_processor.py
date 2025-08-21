from __future__ import annotations

"""Utility functions for aspect analysis and logging.

This module provides simple analysis helpers that log results under
``data/aspects``. Each analyser returns a dictionary of metrics while
appending the same information to an aspect-specific log file for
auditing and cross-layer referencing.
"""

import json
from datetime import datetime
from pathlib import Path
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


def analyze_geometric(data: Any) -> Dict[str, Any]:
    """Analyze simple geometric properties of ``data`` and log them."""

    try:
        size = len(data)  # type: ignore[arg-type]
    except Exception:
        size = len(str(data))
    analysis = {"data": str(data), "dimensions": size}
    _log("geometric", analysis)
    return analysis


def analyze_emotional(data: Any) -> Dict[str, Any]:
    """Basic emotional analysis for sequences or text."""

    try:
        values = [float(v) for v in data]  # type: ignore[iteration-over-obj]
        mean = sum(values) / len(values) if values else 0.0
        analysis = {"mean": mean, "count": len(values)}
    except Exception:
        text = str(data)
        analysis = {"text": text, "length": len(text)}
    _log("emotional", analysis)
    return analysis


def analyze_temporal(value: Any) -> Dict[str, Any]:
    """Record temporal metrics for ``value`` and log them."""

    try:
        dt = datetime.fromisoformat(str(value))
    except Exception:
        try:
            dt = datetime.utcfromtimestamp(float(value))
        except Exception:
            dt = datetime.utcnow()
    analysis = {"value": str(value), "hour": dt.hour, "weekday": dt.weekday()}
    _log("temporal", analysis)
    return analysis


def analyze_spatial(data: Any) -> Dict[str, Any]:
    """Analyze simple spatial characteristics and log them."""

    try:
        values = [float(v) for v in data]  # type: ignore[iteration-over-obj]
        analysis = {
            "count": len(values),
            "min": min(values) if values else 0.0,
            "max": max(values) if values else 0.0,
        }
    except Exception:
        text = str(data)
        analysis = {"text": text, "length": len(text)}
    _log("spatial", analysis)
    return analysis


def analyze_ritual(text: str) -> Dict[str, Any]:
    """Perform a minimal ritual analysis of ``text`` and log it."""

    words = text.split()
    analysis = {"text": text, "word_count": len(words)}
    _log("ritual", analysis)
    return analysis


__all__ = [
    "analyze_phonetic",
    "analyze_semantic",
    "analyze_geometric",
    "analyze_emotional",
    "analyze_temporal",
    "analyze_spatial",
    "analyze_ritual",
    "ASPECT_LOG_DIR",
]
