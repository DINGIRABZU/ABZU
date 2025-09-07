"""WebRTC video/audio stream management with per-agent sessions."""

from __future__ import annotations

from communication.webrtc_gateway import (
    AvatarAudioTrack,
    AvatarVideoTrack,
    WebRTCGateway,
    WebRTCServer,
    configure_tracks,
    enable_audio_track,
    enable_video_track,
)

from .session_manager import AvatarSessionManager, session_manager

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
