"""Parity tests for numeric.cosine_similarity."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "NEOABZU" / "target" / "debug"))

import neoabzu_numeric
import vector_memory


def test_cosine_similarity_matches_legacy():
    a = [1.0, 0.0, 1.0]
    b = [0.0, 1.0, 1.0]
    new = neoabzu_numeric.cosine_similarity(a, b)
    old = vector_memory.cosine_similarity(a, b)
    assert abs(new - old) < 1e-8
