from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
ARC_DIR = ROOT / "web_console"


def test_arcade_html_renders_insert_coin() -> None:
    html = (ARC_DIR / "arcade.html").read_text(encoding="utf-8")
    assert "insert coin" in html.lower()


def test_arcade_buttons_and_endpoints() -> None:
    html = BeautifulSoup((ARC_DIR / "arcade.html").read_text(), "html.parser")
    ids = ["ignite-btn", "memory-btn", "handover-btn"]
    for _id in ids:
        assert html.find("button", id=_id) is not None

    js = (ARC_DIR / "main.js").read_text()
    assert "${BASE_URL}/ignite" in js
    assert "${BASE_URL}/memory/query" in js
    assert "${BASE_URL}/handover" in js
