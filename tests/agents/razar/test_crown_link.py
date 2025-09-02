"""Tests for crown link."""

import asyncio
import json
from pathlib import Path

import websockets

from agents.razar import crown_link
from agents.razar.crown_link import BlueprintReport, CrownLink, StatusUpdate


async def _mock_handler(websocket):
    msg = await websocket.recv()
    data = json.loads(msg)
    if data["type"] == "status":
        assert "component" in data
        reply = {"ack": data["component"]}
    else:
        assert data["type"] == "report"
        assert "blueprint_excerpt" in data
        reply = {"suggestions": "use dataclasses", "revisions": "refactor"}
    await websocket.send(json.dumps(reply))


def test_send_report_and_log(tmp_path):
    crown_link.LOG_PATH = tmp_path / "dialogues.json"

    async def run():
        server = await websockets.serve(_mock_handler, "127.0.0.1", 8765)
        async with server:
            async with CrownLink("ws://127.0.0.1:8765") as link:
                resp = await link.send_report(BlueprintReport("bp", "log"))
        return resp

    resp = asyncio.run(run())
    assert resp["suggestions"] == "use dataclasses"
    assert crown_link.LOG_PATH.exists()
    entry = json.loads(Path(crown_link.LOG_PATH).read_text().splitlines()[0])
    assert entry["request"]["blueprint_excerpt"] == "bp"
    assert entry["response"]["suggestions"] == "use dataclasses"


def test_send_status(tmp_path):
    crown_link.LOG_PATH = tmp_path / "dialogues.json"

    async def run():
        server = await websockets.serve(_mock_handler, "127.0.0.1", 8765)
        async with server:
            async with CrownLink("ws://127.0.0.1:8765") as link:
                resp = await link.send_status(StatusUpdate("engine", "ok"))
        return resp

    resp = asyncio.run(run())
    assert resp["ack"] == "engine"
