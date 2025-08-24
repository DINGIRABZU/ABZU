"""Unified command line interface for Spiral OS tools.

This module exposes a small wrapper around common developer tasks. It is
lightweight and avoids importing heavy dependencies until a command is
invoked.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Callable, List, Optional


def _start(_: argparse.Namespace) -> None:
    """Launch the Spiral OS startup sequence."""
    from start_spiral_os import main as start_main

    start_main([])


def _test(_: argparse.Namespace) -> None:
    """Execute the project's test suite using ``pytest``."""
    import pytest

    raise SystemExit(pytest.main([]))


def _profile(_: argparse.Namespace) -> None:
    """Profile the startup sequence using ``cProfile``."""
    import cProfile
    from start_spiral_os import main as start_main  # noqa: F401

    cProfile.runctx("start_main([])", globals(), locals())


def _play_music(args: argparse.Namespace) -> None:
    """Run the music demo on ``args.audio``."""
    demo_script = Path(__file__).resolve().parents[1] / "run_song_demo.py"
    cmd = [sys.executable, str(demo_script), args.audio]
    subprocess.run(cmd, check=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Spiral OS helper commands")
    sub = parser.add_subparsers(dest="command", required=True)

    start_p = sub.add_parser("start", help="Launch the Spiral OS stack")
    start_p.set_defaults(func=_start)

    test_p = sub.add_parser("test", help="Run the test suite")
    test_p.set_defaults(func=_test)

    prof_p = sub.add_parser("profile", help="Profile system startup")
    prof_p.set_defaults(func=_profile)

    music_p = sub.add_parser("play-music", help="Analyze a local audio file")
    music_p.add_argument("audio", help="Path to an MP3 or WAV file")
    music_p.set_defaults(func=_play_music)

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    """Entry point for the command line script."""
    parser = build_parser()
    args = parser.parse_args(argv)
    func: Callable[[argparse.Namespace], None] = args.func
    func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
