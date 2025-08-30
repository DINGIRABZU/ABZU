"""Tests for video stream helper utilities."""

from __future__ import annotations

import asyncio
import importlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

__version__ = "0.0.0"


@pytest.fixture()
def vs(monkeypatch: pytest.MonkeyPatch):
    """Provide a ``video_stream`` module with core dependencies stubbed."""
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
    setattr(
        core_stub,
        "load_config",
        lambda: SimpleNamespace(services=SimpleNamespace(animation_service_url="")),
    )
    monkeypatch.setitem(sys.modules, "core", core_stub)
    vs_module = importlib.import_module("video_stream")

    async def _close_peers(self) -> None:
        coros = [pc.close() for pc in list(vs_module._pcs)]
        vs_module._pcs.clear()
        for coro in coros:
            await coro
        vs_module._active_track = None

    monkeypatch.setattr(vs_module.WebRTCStreamProcessor, "close_peers", _close_peers)

    yield vs_module
    sys.modules.pop("video_stream", None)


def test_cue_colour_deterministic(vs):
    track = vs.AvatarVideoTrack()
    assert np.array_equal(track._cue_colour("a"), track._cue_colour("a"))
    assert not np.array_equal(track._cue_colour("a"), track._cue_colour("b"))


def test_apply_cue_marks_corners(vs):
    track = vs.AvatarVideoTrack()
    frame = np.zeros((20, 20, 3), dtype=np.uint8)
    track._style = "style"
    out = track._apply_cue(frame)
    color = track._cue_colour("style")
    assert (out[:10, :10] == color).all()
    assert (out[-10:, -10:] == color).all()


def test_close_peers_clears_state(vs):
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


def test_avatar_audio_track_recv(vs):
    track = vs.AvatarAudioTrack()
    frame = asyncio.run(track.recv())
    assert frame.sample_rate == track._sr


def test_avatar_video_track_recv(vs):
    track = vs.AvatarVideoTrack()
    frame = asyncio.run(track.recv())
    assert frame.width == 20
    assert frame.height == 20


def test_avatar_audio_track_from_file(vs, monkeypatch, tmp_path):
    dummy_sf = ModuleType("soundfile")
    dummy_sf.read = lambda path, dtype=None: (np.zeros((1, 80), dtype="int16"), 8000)
    monkeypatch.setattr(vs, "sf", dummy_sf)
    track = vs.AvatarAudioTrack(tmp_path / "a.wav")
    asyncio.run(track.recv())
    assert track._index == track._samples


def test_avatar_audio_update_endpoint(vs, tmp_path):
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
