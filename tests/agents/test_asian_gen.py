from __future__ import annotations

from pathlib import Path

import sentencepiece as spm

from agents.asian_gen.creative_engine import CreativeEngine


def _build_sp_model(tmp_path: Path) -> Path:
    text_file = tmp_path / "text.txt"
    text_file.write_text("hello world\nこんにちは 世界\n")
    spm.SentencePieceTrainer.train(
        input=str(text_file), model_prefix=str(tmp_path / "m"), vocab_size=32
    )
    return tmp_path / "m.model"


def test_locale_routed_generation(monkeypatch):
    class DummyTokenizer:
        lang_code_to_id = {"ja": 7}

    class DummyAutoTokenizer:
        @staticmethod
        def from_pretrained(model_name, local_files_only=True):
            return DummyTokenizer()

    class DummyPipe:
        def __call__(
            self,
            prompt,
            max_new_tokens,
            num_return_sequences,
            forced_bos_token_id=None,
        ):
            assert forced_bos_token_id == 7
            return [{"generated_text": "response"}]

    monkeypatch.setattr(
        "agents.asian_gen.creative_engine.AutoTokenizer", DummyAutoTokenizer
    )
    monkeypatch.setattr(
        "agents.asian_gen.creative_engine.pipeline", lambda *a, **k: DummyPipe()
    )

    engine = CreativeEngine()
    text = engine.generate("hello", locale="ja")
    assert text == "response"


def test_sentencepiece_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr("agents.asian_gen.creative_engine.AutoTokenizer", None)
    monkeypatch.setattr("agents.asian_gen.creative_engine.pipeline", None)

    model_path = _build_sp_model(tmp_path)
    engine = CreativeEngine(spm_path=str(model_path))

    output = engine.generate("hello", locale="ja")
    assert isinstance(output, str) and output
