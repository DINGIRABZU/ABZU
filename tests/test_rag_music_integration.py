import sys
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub heavy optional packages
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))

import qnl_engine
import rag_music_oracle as rmo
import vector_memory


def test_rag_music_pipeline(tmp_path, monkeypatch):
    pdf = tmp_path / "book.pdf"
    pdf.write_text("Hex secrets", encoding="utf-8")
    audio = tmp_path / "clip.wav"
    audio.write_bytes(b"\x00\x00")

    ingested = {}

    def fake_add_vector(text, meta):
        ingested["text"] = text
        ingested["meta"] = meta

    monkeypatch.setattr(vector_memory, "add_vector", fake_add_vector)
    vector_memory.add_vector("Hex secrets", {"SOURCE_TYPE": "PDF", "SOURCE_PATH": str(pdf)})

    features = {"emotion": "joy", "tempo": 90.0, "pitch": 440.0}
    monkeypatch.setattr(rmo, "analyze_audio", lambda p: features)

    called = {}

    def fake_query(query, top_n=5):
        called["query"] = query
        return [{"snippet": ingested.get("text", ""), "metadata": ingested.get("meta", {})}]

    monkeypatch.setattr(rmo.rag_engine, "query", fake_query)

    hex_called = {}

    def fake_hex_to_song(hex_input, duration_per_byte=1.0, sample_rate=44100):
        hex_called["value"] = hex_input
        return [], b""

    monkeypatch.setattr(qnl_engine, "hex_to_song", fake_hex_to_song)

    def fake_compose(emotion, ritual, archetype=None):
        qnl_engine.hex_to_song("deadbeef")
        return tmp_path / "out.wav"

    monkeypatch.setattr(rmo.play_ritual_music, "compose_ritual_music", fake_compose)

    text, out = rmo.answer("What is hidden?", audio, play=True)

    assert out == tmp_path / "out.wav"
    assert "joy" in text
    assert called["query"] == "What is hidden? emotion:joy tempo:90.0 pitch:440.0"
    assert hex_called["value"] == "deadbeef"
    assert ingested["meta"]["SOURCE_PATH"] == str(pdf)

