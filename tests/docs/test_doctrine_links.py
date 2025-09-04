from pathlib import Path


DOC_INDEX = Path(__file__).resolve().parents[2] / "docs" / "INDEX.md"


def _index_text() -> str:
    return DOC_INDEX.read_text(encoding="utf-8")


def test_absolute_protocol_listed() -> None:
    assert "The_Absolute_Protocol.md" in _index_text()


def test_contributor_checklist_listed() -> None:
    assert "contributor_checklist.md" in _index_text()


def test_chakra_metrics_listed() -> None:
    assert "chakra_metrics.md" in _index_text()
