"""Additional tests for music generation streaming and parameters."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("omegaconf")

import music_generation as mg


@pytest.fixture()
def tmp_output(tmp_path, monkeypatch):
    monkeypatch.setattr(mg, "OUTPUT_DIR", tmp_path)
    return tmp_path


def test_duration_and_seed_parameters(tmp_output, monkeypatch):
    captured = {}

    def fake_pipeline(task, model):
        assert task == "text-to-audio"
        assert model == mg.MODEL_IDS["musicgen"]

        def call(prompt, **params):
            captured["prompt"] = prompt
            captured["params"] = params
            length = params["duration"]
            return [{"audio": b"x" * length}]

        return call

    monkeypatch.setattr(mg, "hf_pipeline", fake_pipeline)

    out = mg.generate_from_text(
        "beat",
        duration=4,
        seed=123,
        temperature=0.5,
    )
    assert isinstance(out, Path)
    assert out.read_bytes() == b"x" * 4
    assert captured["params"] == {
        "temperature": 0.5,
        "duration": 4,
        "stream": False,
        "seed": 123,
    }


def test_streaming_yields_chunks(tmp_output, monkeypatch):
    def fake_pipeline(task, model):
        assert task == "text-to-audio"
        assert model == mg.MODEL_IDS["musicgen"]

        def gen(prompt, **params):
            assert params["stream"] is True
            yield {"audio": b"a"}
            yield {"audio": b"b"}

        return gen

    monkeypatch.setattr(mg, "hf_pipeline", fake_pipeline)

    stream = mg.generate_from_text("beat", stream=True)
    assert list(stream) == [b"a", b"b"]
