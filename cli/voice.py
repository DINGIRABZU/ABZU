from __future__ import annotations

"""Command line tool to synthesize speech and play or stream it."""

import argparse
import logging
from pathlib import Path

import numpy as np

from INANNA_AI import speaking_engine
from core import avatar_expression_engine
from connectors import webrtc_connector
from crown_config import settings

logger = logging.getLogger(__name__)


def play_frame(frame: np.ndarray) -> None:
    """Render ``frame`` to the local display if OpenCV is available."""
    try:  # pragma: no cover - optional dependency
        import cv2  # type: ignore
    except Exception:  # pragma: no cover - gracefully handle missing cv2
        return
    cv2.imshow("INANNA", frame)
    cv2.waitKey(1)


def send_frame(frame: np.ndarray) -> None:
    """Forward ``frame`` to an animation subsystem via HTTP."""
    try:  # pragma: no cover - optional dependencies
        import cv2  # type: ignore
        import httpx
    except Exception:  # pragma: no cover - dependencies may be missing
        return
    url = settings.animation_service_url or "http://localhost:8000/frame"
    try:
        ok, buf = cv2.imencode(".jpg", frame)
        if ok:
            httpx.post(url, content=buf.tobytes())
    except Exception as exc:  # pragma: no cover - network may fail
        logger.debug("failed to forward frame: %s", exc)


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
        "--stream",
        action="store_true",
        help="Send avatar frames to a remote animation service",
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

    if args.play or args.stream:
        try:
            for frame in avatar_expression_engine.stream_avatar_audio(Path(path)):
                if args.play:
                    try:
                        play_frame(frame)
                    except Exception as exc:  # pragma: no cover - optional backend
                        logger.error("audio playback failed: %s", exc)
                        break
                if args.stream:
                    try:
                        send_frame(frame)
                    except Exception as exc:  # pragma: no cover - network may fail
                        logger.error("frame forward failed: %s", exc)
        except Exception as exc:  # pragma: no cover - backend may be missing
            logger.error("audio backend initialization failed: %s", exc)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
