"""CLI for recording samples and synthesizing speech via :mod:`EmotiVoice`."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from audio.voice_cloner import VoiceCloner

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture voice samples and synthesize speech",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    rec = sub.add_parser("capture", help="Record a voice sample")
    rec.add_argument("path", help="Output WAV path")
    rec.add_argument("--speaker", default="user", help="Speaker profile name")
    rec.add_argument("--seconds", type=float, default=3.0, help="Recording length")
    rec.add_argument("--sr", type=int, default=22_050, help="Sample rate")

    syn = sub.add_parser("synthesize", help="Generate speech using a sample")
    syn.add_argument("text", help="Text to speak")
    syn.add_argument("out", help="Output WAV path")
    syn.add_argument("--sample", required=True, help="Path to captured sample")
    syn.add_argument("--speaker", default="user", help="Speaker profile name")
    syn.add_argument("--emotion", default="neutral", help="Emotion for TTS")

    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for the voice cloning utility."""

    args = _build_parser().parse_args(argv)
    cloner = VoiceCloner()

    if args.cmd == "capture":
        try:
            cloner.capture_sample(
                Path(args.path),
                seconds=args.seconds,
                sr=args.sr,
                speaker=args.speaker,
            )
        except RuntimeError as exc:  # pragma: no cover - missing deps
            logger.error("%s", exc)
    elif args.cmd == "synthesize":
        cloner.samples[args.speaker] = Path(args.sample)
        try:
            _, mos = cloner.synthesize(
                args.text,
                Path(args.out),
                speaker=args.speaker,
                emotion=args.emotion,
            )
            logger.info("Synthesis MOS=%.2f", mos)
        except RuntimeError as exc:  # pragma: no cover - missing deps
            logger.error("%s", exc)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
