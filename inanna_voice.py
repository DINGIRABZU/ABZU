from __future__ import annotations

"""Command line tool to synthesize speech and play or stream it."""

import argparse
from pathlib import Path

from INANNA_AI import speaking_engine
from core import avatar_expression_engine
from connectors import webrtc_connector


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
        for _ in avatar_expression_engine.stream_avatar_audio(Path(path)):
            pass


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
