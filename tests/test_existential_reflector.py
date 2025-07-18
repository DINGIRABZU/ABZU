import sys
from types import ModuleType
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI.existential_reflector import ExistentialReflector


class DummyResponse:
    def __init__(self, data: dict[str, str]):
        self._data = data
        self.text = data.get("description", "")

    def json(self):
        return self._data

    def raise_for_status(self):
        return None


def test_reflect_on_identity(tmp_path, monkeypatch):
    ina = tmp_path / "INANNA_AI"
    qnl = tmp_path / "QNL_LANGUAGE"
    ina.mkdir()
    qnl.mkdir()
    (ina / "a.md").write_text("hello", encoding="utf-8")
    (qnl / "b.md").write_text("world", encoding="utf-8")

    audit = tmp_path / "audit_logs"

    import INANNA_AI.existential_reflector as er
    monkeypatch.setattr(er, "INANNA_DIR", ina)
    monkeypatch.setattr(er, "QNL_DIR", qnl)
    monkeypatch.setattr(er, "AUDIT_DIR", audit)
    monkeypatch.setattr(er, "INSIGHTS_FILE", audit / "existential_insights.txt")

    dummy = ModuleType("requests")
    dummy.post = lambda *a, **k: DummyResponse({"description": "I am"})
    monkeypatch.setattr(er, "requests", dummy)

    desc = ExistentialReflector.reflect_on_identity()
    assert desc == "I am"
    assert (audit / "existential_insights.txt").read_text() == "I am"


def test_reflect_existence_function(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(ExistentialReflector, "reflect_on_identity", lambda: "desc")
    from INANNA_AI_AGENT import INANNA_AI
    monkeypatch.setattr(inanna_ai, "ExistentialReflector", ExistentialReflector)
    out = inanna_ai.reflect_existence()
    captured = capsys.readouterr().out
    assert out == "desc"
    assert "desc" in captured


def test_existential_header(monkeypatch, tmp_path):
    monkeypatch.setenv("GLM_API_KEY", "sek")
    import importlib
    er = importlib.reload(
        __import__("INANNA_AI.existential_reflector", fromlist=["ExistentialReflector"])
    )

    ina = tmp_path / "INANNA_AI"
    qnl = tmp_path / "QNL_LANGUAGE"
    ina.mkdir()
    qnl.mkdir()
    (ina / "a.md").write_text("x", encoding="utf-8")

    monkeypatch.setattr(er, "INANNA_DIR", ina)
    monkeypatch.setattr(er, "QNL_DIR", qnl)
    monkeypatch.setattr(er, "AUDIT_DIR", tmp_path)
    monkeypatch.setattr(er, "INSIGHTS_FILE", tmp_path / "i.txt")

    hdr = {}
    dummy = ModuleType("requests")

    def post(url, json=None, timeout=10, headers=None):
        hdr["h"] = headers
        return DummyResponse({"description": "A"})

    dummy.post = post
    monkeypatch.setattr(er, "requests", dummy)

    er.ExistentialReflector.reflect_on_identity()
    assert hdr["h"] == {"Authorization": "Bearer sek"}


def test_reflect_on_dilemma(monkeypatch, tmp_path):
    import INANNA_AI.existential_reflector as er
    from INANNA_AI import context

    audit = tmp_path / "audit_logs"
    monkeypatch.setattr(er, "AUDIT_DIR", audit)
    monkeypatch.setattr(er, "INSIGHTS_FILE", audit / "i.txt")

    # reset context
    context._CONTEXT.clear()

    payload = {}
    dummy = ModuleType("requests")

    def post(url, json=None, timeout=10, headers=None):
        payload.update(json or {})
        return DummyResponse({"description": "reflect"})

    dummy.post = post
    monkeypatch.setattr(er, "requests", dummy)

    desc = er.ExistentialReflector.reflect_on_dilemma("What is truth?", "joy")

    assert desc == "reflect"
    assert payload["prompt"] == "What is truth?"
    assert payload["emotion"] == "joy"
    assert "context" in payload and payload["context"] == ["What is truth?"]
    assert (audit / "i.txt").read_text() == "reflect"
