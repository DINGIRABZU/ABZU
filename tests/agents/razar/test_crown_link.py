import asyncio
import json
from pathlib import Path

import websockets

from agents.razar import crown_link
from agents.razar.crown_link import BlueprintReport, CrownLink


async def _mock_handler(websocket):
    msg = await websocket.recv()
    data = json.loads(msg)
    assert data["type"] == "report"
    assert "blueprint_excerpt" in data
    reply = {"suggestions": "use dataclasses", "revisions": "refactor"}
    await websocket.send(json.dumps(reply))


def test_exchange(tmp_path):
    crown_link.LOG_PATH = tmp_path / "dialogues.json"

    async def run():
        server = await websockets.serve(_mock_handler, "127.0.0.1", 8765)
        async with server:
            async with CrownLink("ws://127.0.0.1:8765") as link:
                resp = await link.exchange(BlueprintReport("bp", "log"))
        return resp

    resp = asyncio.run(run())
    assert resp["suggestions"] == "use dataclasses"
    assert crown_link.LOG_PATH.exists()
    entry = json.loads(Path(crown_link.LOG_PATH).read_text().splitlines()[0])
    assert entry["request"]["blueprint_excerpt"] == "bp"
    assert entry["response"]["suggestions"] == "use dataclasses"
