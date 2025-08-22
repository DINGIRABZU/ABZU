from __future__ import annotations

import music_generation


def test_generate_from_text_includes_emotion_and_tempo(monkeypatch, tmp_path):
    captured = {}

    class DummyPipe:
        def __call__(self, prompt: str):
            captured["prompt"] = prompt
            return [{"audio": b"data"}]

    monkeypatch.setattr(music_generation, "hf_pipeline", lambda *_, **__: DummyPipe())
    monkeypatch.setattr(music_generation, "OUTPUT_DIR", tmp_path)

    path = music_generation.generate_from_text("melody", emotion="joy", tempo=120)
    assert "joy" in captured["prompt"]
    assert "120" in captured["prompt"]
    assert path.exists()
