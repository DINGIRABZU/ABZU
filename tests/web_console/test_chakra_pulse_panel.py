from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GD_DIR = ROOT / "web_console" / "game_dashboard"


def test_dashboard_imports_chakra_pulse() -> None:
    js = (GD_DIR / "dashboard.js").read_text(encoding="utf-8")
    assert "chakraPulse.js" in js
    assert "ChakraPulse" in js


def test_chakra_pulse_component_has_id() -> None:
    comp = (GD_DIR / "chakraPulse.js").read_text(encoding="utf-8")
    assert "chakra-pulse" in comp


def test_index_styles_panel() -> None:
    html = (GD_DIR / "index.html").read_text(encoding="utf-8")
    assert "#chakra-pulse" in html
