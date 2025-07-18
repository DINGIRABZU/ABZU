import sys
from pathlib import Path
import numpy as np

# Allow importing project modules
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from MUSIC_FOUNDATION import qnl_utils
from MUSIC_FOUNDATION.qnl_utils import chroma_to_qnl, generate_qnl_structure, quantum_embed


def test_generate_qnl_structure():
    chroma = np.zeros(12)
    chroma[0] = 1.0
    chroma[4] = 0.5
    tempo = 120.0

    data = generate_qnl_structure(chroma, tempo, metadata={"title": "x"})

    assert data["tempo"] == tempo
    assert data["metadata"]["title"] == "x"
    assert len(data["structure"]) == 4
    assert data["structure"][0]["glyph"] == '❣⟁'
    assert data["qnl_output"][0].startswith('❣⟁')


def test_chroma_to_qnl_order_and_notes():
    chroma = np.array([
        0.1,  # C
        0.3,  # C#
        0.2,  # D
        0.05, # D#
        0.4,  # E
        0.0,  # F
        0.0,  # F#
        0.0,  # G
        0.0,  # G#
        0.0,  # A
        0.0,  # A#
        0.0,  # B
    ])

    phrases = chroma_to_qnl(chroma)
    assert [p["note"] for p in phrases] == ["E", "C#", "D", "C"]
    assert phrases[0]["glyph"] == '🪞♾'


def test_quantum_embed(monkeypatch):
    calls = []

    class DummyModel:
        def encode(self, text: str):
            calls.append(text)
            return np.array([1.0, 2.0])

    monkeypatch.setattr(qnl_utils, "SentenceTransformer", lambda name: DummyModel())
    qnl_utils._MODEL = None
    vec = quantum_embed("hello")
    assert calls == ["hello"]
    assert vec.tolist() == [1.0, 2.0]
