"""Tests for learning mutator."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import learning_mutator as lm


def test_propose_mutations(tmp_path, monkeypatch):
    matrix = {
        "good": {"counts": {"total": 5, "success": 5}},
        "bad": {"counts": {"total": 4, "success": 1}},
        "ugly": {"counts": {"total": 4, "success": 1}},
    }
    intent_file = tmp_path / "intent.json"
    intent_file.write_text(
        json.dumps({"bad": {"synonyms": ["awful"]}}), encoding="utf-8"
    )
    monkeypatch.setattr(
        lm, "load_intents", lambda path=intent_file: json.loads(intent_file.read_text())
    )

    suggestions = lm.propose_mutations(matrix)

    assert any("awful" in s and "bad" in s for s in suggestions)
    assert any("ugly" in s and "good" in s for s in suggestions)


def test_main_writes_mutation_file(tmp_path, monkeypatch):
    mfile = tmp_path / "mutations.txt"
    monkeypatch.setattr(lm, "MUTATION_FILE", mfile)
    monkeypatch.setattr(lm, "load_insights", lambda path=None: {})
    monkeypatch.setattr(lm, "propose_mutations", lambda data: ["a", "b"])
    lm.main(["--run"])
    assert mfile.read_text(encoding="utf-8").splitlines() == ["a", "b"]


def test_main_rolls_back_on_write_error(tmp_path, monkeypatch):
    mfile = tmp_path / "mutations.txt"
    mfile.write_text("old", encoding="utf-8")
    monkeypatch.setattr(lm, "MUTATION_FILE", mfile)
    monkeypatch.setattr(lm, "load_insights", lambda path=None: {})
    monkeypatch.setattr(lm, "propose_mutations", lambda data: ["new"])
    orig_write = Path.write_text

    def fail_write(self, *args, **kwargs):
        if self == mfile:
            raise OSError("nope")
        return orig_write(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_write)
    with pytest.raises(OSError):
        lm.main(["--run"])
    assert mfile.read_text(encoding="utf-8") == "old"


def test_propose_mutations_emotion_driven(monkeypatch):
    matrix = {"meh": {"counts": {"total": 4, "success": 1}}}
    monkeypatch.setattr(lm, "load_intents", lambda path=lm.INTENT_FILE: {})
    monkeypatch.setattr(
        lm.emotion_registry, "get_current_layer", lambda: "rubedo_layer"
    )
    monkeypatch.setattr(lm.emotion_registry, "get_last_emotion", lambda: "anger")
    monkeypatch.setattr(lm.emotion_registry, "get_resonance_level", lambda: 0.9)

    suggestions = lm.propose_mutations(matrix)

    assert any("nigredo_layer" in s for s in suggestions)
    assert any("Fuse rubedo_layer with citrinitas_layer" in s for s in suggestions)
