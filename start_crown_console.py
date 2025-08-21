#!/usr/bin/env python3
"""Run Crown services and video stream with graceful shutdown."""
from __future__ import annotations
import json
import signal
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
import emotional_state


ROOT = Path(__file__).resolve().parent

GLYPH_META = ROOT / "data" / "last_glyph.json"

_GLYPHS = {
    "joy": "🌀😊",
    "sadness": "🌀😢",
    "anger": "🌀😠",
    "fear": "🌀😨",
    "neutral": "🌀",
}


def main() -> None:
    """Launch console and video stream then wait for exit."""
    load_dotenv(ROOT / "secrets.env")

    crown_proc = subprocess.Popen(["bash", str(ROOT / "start_crown_console.sh")])
    stream_proc = subprocess.Popen([sys.executable, str(ROOT / "video_stream.py")])
    procs = [crown_proc, stream_proc]

    def _terminate(*_args: object) -> None:
        for p in procs:
            if p.poll() is None:
                p.terminate()
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()

    signal.signal(signal.SIGINT, _terminate)
    signal.signal(signal.SIGTERM, _terminate)

    last_emotion: str | None = None
    last_glyph: dict[str, str] | None = None
    try:
        while any(p.poll() is None for p in procs):
            emotion = emotional_state.get_last_emotion() or "neutral"
            if emotion != last_emotion:
                glyph = _GLYPHS.get(emotion, _GLYPHS["neutral"])
                print(f"{glyph} {emotion}")
                last_emotion = emotion
            if GLYPH_META.exists():
                try:
                    data = json.loads(GLYPH_META.read_text(encoding="utf-8"))
                except Exception:
                    data = {}
                if data and data != last_glyph:
                    print(f"glyph: {data.get('path')} :: {data.get('phrase')}")
                    last_glyph = data
            time.sleep(0.5)
    finally:
        _terminate()

    crown_code = getattr(crown_proc, "returncode", 0) or 0
    stream_code = getattr(stream_proc, "returncode", 0) or 0
    if crown_code:
        print(f"Error: crown process exited with code {crown_code}")
        raise SystemExit(crown_code)
    if stream_code:
        print(f"Error: stream process exited with code {stream_code}")
        raise SystemExit(stream_code)


if __name__ == "__main__":
    main()
