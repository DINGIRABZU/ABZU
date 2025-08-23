"""Tests for video stream helper utilities."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import ModuleType

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Provide minimal stubs for modules imported by video_stream
core_stub = ModuleType("core")
avatar_mod = ModuleType("avatar_expression_engine")
setattr(
    avatar_mod,
    "stream_avatar_audio",
    lambda path: iter([np.zeros((20, 20, 3), dtype=np.uint8)]),
)
setattr(core_stub, "avatar_expression_engine", avatar_mod)
video_mod = ModuleType("video_engine")
setattr(
    video_mod,
    "generate_avatar_stream",
    lambda: (np.zeros((20, 20, 3), dtype=np.uint8) for _ in iter(int, 1)),
)
setattr(core_stub, "video_engine", video_mod)
sys.modules.setdefault("core", core_stub)

import video_stream as vs  # noqa: E402


def test_cue_colour_deterministic():
    track = vs.AvatarVideoTrack()
    assert np.array_equal(track._cue_colour("a"), track._cue_colour("a"))
    assert not np.array_equal(track._cue_colour("a"), track._cue_colour("b"))


def test_apply_cue_marks_corners():
    track = vs.AvatarVideoTrack()
    frame = np.zeros((20, 20, 3), dtype=np.uint8)
    track._style = "style"
    out = track._apply_cue(frame)
    color = track._cue_colour("style")
    assert (out[:10, :10] == color).all()
    assert (out[-10:, -10:] == color).all()


def test_close_peers_clears_state():
    pc_calls: list[str] = []

    async def dummy_close():
        pc_calls.append("closed")

    class DummyPC:
        def __hash__(self) -> int:  # pragma: no cover - trivial
            return 1

        async def close(self) -> None:
            await dummy_close()

    pc = DummyPC()
    vs._pcs.add(pc)
    vs._active_track = object()
    asyncio.run(vs.WebRTCStreamProcessor().close_peers())
    assert pc_calls == ["closed"]
    assert not vs._pcs
    assert vs._active_track is None


def test_avatar_audio_track_recv():
    track = vs.AvatarAudioTrack()
    frame = asyncio.run(track.recv())
    assert frame.sample_rate == track._sr


def test_avatar_video_track_recv():
    track = vs.AvatarVideoTrack()
    frame = asyncio.run(track.recv())
    assert frame.width == 20
    assert frame.height == 20


def test_avatar_audio_track_from_file(monkeypatch, tmp_path):
    dummy_sf = ModuleType("soundfile")
    dummy_sf.read = lambda path, dtype=None: (np.zeros((1, 80), dtype="int16"), 8000)
    monkeypatch.setattr(vs, "sf", dummy_sf)
    track = vs.AvatarAudioTrack(tmp_path / "a.wav")
    asyncio.run(track.recv())
    assert track._index == track._samples


def test_avatar_audio_update_endpoint(tmp_path):
    class DummyRequest:
        def __init__(self, path: Path) -> None:
            self._path = path

        async def json(self) -> dict[str, str]:
            return {"path": str(self._path)}

    class DummyTrack:
        def __init__(self) -> None:
            self.updated: Path | None = None

        def update_audio(self, path: Path) -> None:
            self.updated = path

    track = DummyTrack()
    vs._active_track = track
    processor = vs.WebRTCStreamProcessor()
    result = asyncio.run(processor.avatar_audio(DummyRequest(tmp_path / "a.wav")))
    assert result == {"status": "ok"}
    assert track.updated == tmp_path / "a.wav"
