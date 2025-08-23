from __future__ import annotations

from pathlib import Path
import sys
import types

from fastapi.testclient import TestClient

import introspection_api
from src.lwm import LargeWorldModel, default_lwm
from src.media.video import generate_video


class DummyFFMPEG(types.ModuleType):
    def input(self, *args, **kwargs):
        return "stream"

    def output(self, stream, path):
        return stream

    def run(self, stream, quiet=True):
        return None


def test_large_world_model_from_frames(tmp_path):
    frame = tmp_path / "frame.png"
    frame.write_text("data")
    model = LargeWorldModel()
    scene = model.from_frames([frame])
    assert scene["frames"] == [str(frame)]
    assert scene["points"][0]["index"] == 0


def test_lwm_inspection_route(tmp_path, monkeypatch):
    frame = tmp_path / "frame.png"
    frame.write_text("data")
    monkeypatch.setitem(sys.modules, "ffmpeg", DummyFFMPEG("ffmpeg"))
    video_out = tmp_path / "out.mp4"
    generate_video([frame], video_out, lwm_model=default_lwm)
    client = TestClient(introspection_api.app)
    response = client.get("/lwm/inspect")
    assert response.status_code == 200
    assert response.json()["frames"] == [str(frame)]
