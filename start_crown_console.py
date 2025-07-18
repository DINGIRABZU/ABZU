#!/usr/bin/env python3
"""Run Crown services and video stream with graceful shutdown."""
from __future__ import annotations
import signal
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent


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

    try:
        while any(p.poll() is None for p in procs):
            time.sleep(0.5)
    finally:
        _terminate()


if __name__ == "__main__":
    main()
