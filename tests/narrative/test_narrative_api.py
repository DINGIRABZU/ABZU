from fastapi import FastAPI
from fastapi.testclient import TestClient

import narrative_api


class DummyEngine:
    def __init__(self) -> None:
        self.stories = []

    def log_story(self, text: str) -> None:
        self.stories.append(text)

    def stream_stories(self):
        return iter(self.stories)


narrative_api.narrative_engine = DummyEngine()
narrative_api.story_lookup = type("L", (), {"find": staticmethod(lambda **_: [])})

app = FastAPI()
app.include_router(narrative_api.router)

TOKEN = "demo"


def _client(headers=None):
    headers = headers or {}
    return TestClient(app, headers=headers)


def test_auth_required():
    client = _client()
    r = client.post("/story", json={"text": "hi"})
    assert r.status_code == 401


def test_story_flow():
    client = _client({"Authorization": f"Bearer {TOKEN}"})
    r = client.post("/story", json={"text": "once"})
    assert r.status_code == 200
    r = client.get("/story/log", headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.json()["stories"] == ["once"]
