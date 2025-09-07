"""WebRTC video/audio stream management with per-agent sessions."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

from communication.webrtc_gateway import (
    AvatarAudioTrack,
    AvatarVideoTrack,
    WebRTCGateway,
    WebRTCServer,
    configure_tracks,
    enable_audio_track,
    enable_video_track,
)


class AvatarSessionManager:
    """Maintain avatar tracks keyed by agent identifier."""

    def __init__(self) -> None:
        self.video: Dict[str, AvatarVideoTrack] = {}
        self.audio: Dict[str, AvatarAudioTrack] = {}

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

        return vtrack, atrack

    def update_audio(self, agent: str, path: Path) -> None:
        """Update the lip-sync audio for ``agent``."""

        track = self.video.get(agent)
        if track is None:
            raise KeyError(agent)
        track.update_audio(path)

    def remove(self, agent: str) -> None:
        """Remove any tracks associated with ``agent``."""

        self.video.pop(agent, None)
        self.audio.pop(agent, None)


session_manager = AvatarSessionManager()

processor = WebRTCGateway(session_manager)
router = processor.router
close_peers = processor.close_peers

__all__ = [
    "AvatarAudioTrack",
    "AvatarVideoTrack",
    "AvatarSessionManager",
    "WebRTCGateway",
    "WebRTCServer",
    "configure_tracks",
    "enable_audio_track",
    "enable_video_track",
    "session_manager",
    "router",
    "close_peers",
]
