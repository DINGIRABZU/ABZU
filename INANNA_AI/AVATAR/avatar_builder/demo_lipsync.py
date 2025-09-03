"""Generate a lip-synced avatar animation from text.

This utility synthesizes speech using the existing speaking engine and then
streams avatar frames aligned with the audio to produce a GIF preview. The
demo is intentionally lightweight and avoids external dependencies beyond
the core avatar pipeline.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from core import expressive_output
from INANNA_AI import speaking_engine


def build_demo(text: str, emotion: str, out_file: Path) -> None:
    """Create ``out_file`` showing the avatar mouthing ``text``."""
    audio_path = Path(speaking_engine.synthesize_speech(text, emotion))
    gif_bytes = expressive_output.make_gif(audio_path)
    out_file.write_bytes(gif_bytes)
    print(f"Saved avatar demo to {out_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", nargs="?", default="Hello from INANNA")
    parser.add_argument("--emotion", default="neutral")
    parser.add_argument("--out", type=Path, default=Path("avatar_demo.gif"))
    args = parser.parse_args()
    build_demo(args.text, args.emotion, args.out)


if __name__ == "__main__":  # pragma: no cover - demo script
    main()
