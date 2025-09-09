"""Integration tests for operator arcade UI."""

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from operator_service.api import app


def test_arcade_ui_serves_cuneiform_and_insert_coin() -> None:
    """Arcade page includes welcome glyph, prompt, and memory scan button."""
    with TestClient(app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "insert coin" in html.lower()
    assert "𒀭𒄩𒌆" in html
    soup = BeautifulSoup(html, "html.parser")
    assert soup.find("button", id="memory-scan-btn") is not None
