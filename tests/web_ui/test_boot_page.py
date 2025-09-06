from fastapi.testclient import TestClient

from ui_service import app


def test_boot_page_renders_greeting_and_actions() -> None:
    client = TestClient(app)

    resp = client.get("/boot")

    assert resp.status_code == 200
    html = resp.text
    assert "Silim!" in html
    assert "Load Memory" in html
    assert "Query" in html
    assert "Enter Crown" in html
