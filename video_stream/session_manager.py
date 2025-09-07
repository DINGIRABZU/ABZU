"""Session manager for avatar tracks with heartbeat emission."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

from agents.event_bus import emit_event
from agents.nazarick.chakra_observer import NazarickChakraObserver
from communication.webrtc_gateway import (
    AvatarAudioTrack,
    AvatarVideoTrack,
    enable_audio_track,
    enable_video_track,
)


@dataclass
class _Session:
    chakra: str
    task: asyncio.Task | None


class AvatarSessionManager:
    """Maintain avatar tracks keyed by agent identifier and emit heartbeats."""

    def __init__(self, *, interval: float = 5.0) -> None:
        self.video: Dict[str, AvatarVideoTrack] = {}
        self.audio: Dict[str, AvatarAudioTrack] = {}
        self._info: Dict[str, _Session] = {}
        self.interval = interval

    def get_tracks(
        self, agent: str, audio_path: Optional[Path] = None
    ) -> Tuple[AvatarVideoTrack | None, AvatarAudioTrack | None]:
        """Return (video, audio) tracks for ``agent`` creating them if needed."""

        vtrack = self.video.get(agent)
        if vtrack is None and enable_video_track:
            vtrack = AvatarVideoTrack(audio_path)
            self.video[agent] = vtrack

        atrack = self.audio.get(agent)
        if atrack is None and enable_audio_track:
            atrack = AvatarAudioTrack(audio_path)
            self.audio[agent] = atrack

        if agent not in self._info:
            chakra = NazarickChakraObserver._lookup_chakra(agent)
            task = self._start_heartbeat(agent, chakra)
            self._info[agent] = _Session(chakra, task)
        return vtrack, atrack

    def _start_heartbeat(self, agent: str, chakra: str) -> asyncio.Task | None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # no event loop
            return None

        async def _beat() -> None:
            while agent in self._info:
                emit_event(
                    agent,
                    "heartbeat",
                    {
                        "chakra": chakra,
                        "timestamp": time.time(),
                    },
                )
                await asyncio.sleep(self.interval)

        return loop.create_task(_beat())

    def update_audio(self, agent: str, path: Path) -> None:
        """Update the lip-sync audio for ``agent``."""

        track = self.video.get(agent)
        if track is None:
            raise KeyError(agent)
        track.update_audio(path)

    def remove(self, agent: str) -> None:
        """Remove any tracks associated with ``agent`` and stop heartbeats."""

        self.video.pop(agent, None)
        self.audio.pop(agent, None)
        info = self._info.pop(agent, None)
        if info and info.task is not None:
            info.task.cancel()


session_manager = AvatarSessionManager()

__all__ = ["AvatarSessionManager", "session_manager"]
