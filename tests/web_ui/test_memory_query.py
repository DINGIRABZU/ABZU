from fastapi.testclient import TestClient

from ui_service import app


def test_memory_query_returns_aggregated_results(monkeypatch):
    client = TestClient(app)

    expected = {
        "cortex": [1],
        "vector": [2],
        "spiral": "s",
        "failed_layers": [],
    }

    def fake_query_memory(query: str):  # noqa: ANN001 - simple stub
        return expected

    monkeypatch.setattr("ui_service.query_memory", fake_query_memory)

    resp = client.get("/memory/query", params={"query": "hello"})

    assert resp.status_code == 200
    assert resp.json() == expected
