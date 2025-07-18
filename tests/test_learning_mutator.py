import sys
import json
from pathlib import Path

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
