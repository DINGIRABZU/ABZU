from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS = REPO_ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert_links(text: str) -> None:
    assert "ui/game_dashboard.md" in text
    assert "ui/chakra_pulse.md" in text


def test_ui_docs_present() -> None:
    assert (DOCS / "ui" / "game_dashboard.md").exists()
    assert (DOCS / "ui" / "chakra_pulse.md").exists()


def test_genesis_links() -> None:
    _assert_links(_read(REPO_ROOT / "GENESIS" / "README.md"))


def test_ignition_links() -> None:
    _assert_links(_read(REPO_ROOT / "IGNITION" / "README.md"))


def test_monitoring_links() -> None:
    _assert_links(_read(DOCS / "monitoring.md"))
