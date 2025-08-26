from __future__ import annotations

from agents.asian_gen.creative_engine import CreativeEngine


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


def test_sentencepiece_fallback(monkeypatch):
    monkeypatch.setattr("agents.asian_gen.creative_engine.AutoTokenizer", None)
    monkeypatch.setattr("agents.asian_gen.creative_engine.pipeline", None)

    engine = CreativeEngine()

    output = engine.generate("hello", locale="ja")
    assert isinstance(output, str) and output
