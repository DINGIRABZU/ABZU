from __future__ import annotations

"""Command line tool to synthesize speech and play or stream it."""

import argparse
from pathlib import Path

import numpy as np

from INANNA_AI import speaking_engine
from core import avatar_expression_engine
from connectors import webrtc_connector


def play_frame(frame: np.ndarray) -> None:
    """Render ``frame`` to the local display if OpenCV is available."""
    try:  # pragma: no cover - optional dependency
        import cv2  # type: ignore
    except Exception:  # pragma: no cover - gracefully handle missing cv2
        return
    cv2.imshow("INANNA", frame)
    cv2.waitKey(1)


def send_frame(frame: np.ndarray) -> None:
    """Forward ``frame`` to an animation subsystem.

    The default implementation is a no-op but provides a hook for downstream
    systems. Tests may monkeypatch this function to verify frame handling.
    """
    _ = frame


def main(argv: list[str] | None = None) -> None:
    """Entry point for the voice synthesizer."""
    parser = argparse.ArgumentParser(
        description="Generate speech and optionally play or stream it"
    )
    parser.add_argument("text", help="Text to speak")
    parser.add_argument(
        "--emotion",
        default="neutral",
        help="Emotion driving the tone",
    )
    parser.add_argument(
        "--play",
        action="store_true",
        help="Play audio locally and animate the avatar",
    )
    parser.add_argument(
        "--call",
        action="store_true",
        help="Send audio to connected WebRTC peer",
    )
    args = parser.parse_args(argv)

    speaker = speaking_engine.SpeakingEngine()
    path = speaker.synthesize(args.text, args.emotion)

    if args.call:
        webrtc_connector.start_call(path)

    if args.play:
        for frame in avatar_expression_engine.stream_avatar_audio(Path(path)):
            play_frame(frame)
            send_frame(frame)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
