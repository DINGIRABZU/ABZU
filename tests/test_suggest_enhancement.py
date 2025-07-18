import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI_AGENT import INANNA_AI


def test_suggest_enhancement(tmp_path, monkeypatch):
    audit_dir = tmp_path / "audit_logs"
    inanna_dir = tmp_path / "INANNA_AI"
    audit_dir.mkdir()
    inanna_dir.mkdir()

    analysis = audit_dir / "code_analysis.txt"
    analysis.write_text("keep\nbad idea\nmore", encoding="utf-8")

    monkeypatch.setattr(inanna_ai, "ANALYSIS_PATH", analysis)
    monkeypatch.setattr(inanna_ai, "SUGGESTIONS_FILE", inanna_dir / "suggestions.txt")
    monkeypatch.setattr(inanna_ai, "AUDIT_DIR", audit_dir)
    monkeypatch.setattr(inanna_ai, "SUGGESTIONS_LOG", audit_dir / "suggestions.txt")

    class DummyValidator:
        def __init__(self):
            self.seen = []

        def validate_text(self, text):
            self.seen.append(text)
            return "bad" not in text

    monkeypatch.setattr(inanna_ai, "EthicalValidator", lambda: DummyValidator())

    suggestions = inanna_ai.suggest_enhancement()

    assert suggestions == ["keep", "more"]
    assert (inanna_dir / "suggestions.txt").read_text().splitlines() == ["keep", "more"]
    log_lines = (audit_dir / "suggestions.txt").read_text().splitlines()
    assert len(log_lines) == 2
    assert all("bad" not in l for l in log_lines)

