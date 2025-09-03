"""Tests for generating music via prompt in music_llm_interface."""

from __future__ import annotations

import json
import sys
import types

# Stub heavy dependencies before importing the module
pkg = types.ModuleType("INANNA_AI")
emo = types.ModuleType("INANNA_AI.emotion_analysis")
emo.analyze_audio_emotion = lambda path: {}
pkg.emotion_analysis = emo
sys.modules.setdefault("INANNA_AI", pkg)
sys.modules.setdefault("INANNA_AI.emotion_analysis", emo)

sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))

# Stub orchestrator to avoid heavy imports
orch_mod = types.ModuleType("rag.orchestrator")


class DummyOrch:
    def handle_input(self, text):
        return {"text": text}


orch_mod.MoGEOrchestrator = DummyOrch
rag_pkg = types.ModuleType("rag")
rag_pkg.orchestrator = orch_mod
sys.modules.setdefault("rag", rag_pkg)
sys.modules.setdefault("rag.orchestrator", orch_mod)

import music_llm_interface as mli


def test_generate_and_analyze_calls_components(tmp_path, monkeypatch):
    gen_path = tmp_path / "out.wav"

    def fake_generate(prompt, **kwargs):
        assert prompt == "beat"
        gen_path.write_bytes(b"")
        return gen_path

    def fake_run_interface(path, orchestrator=None):
        assert path == gen_path
        return {"ok": True}

    monkeypatch.setattr(mli.music_generation, "generate_from_text", fake_generate)
    monkeypatch.setattr(mli, "run_interface", fake_run_interface)

    result = mli.generate_and_analyze("beat", emotion="joy")
    assert result == {"ok": True}


def test_cli_prompt_generates_music(tmp_path, monkeypatch, capsys):
    gen_path = tmp_path / "gen.wav"

    def fake_generate(prompt, **kwargs):
        gen_path.write_bytes(b"")
        return gen_path

    def fake_run_interface(path, orchestrator=None):
        assert path == gen_path
        return {"done": True}

    monkeypatch.setattr(mli.music_generation, "generate_from_text", fake_generate)
    monkeypatch.setattr(mli, "run_interface", fake_run_interface)

    mli.main(["--prompt", "beat"])
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"done": True}
