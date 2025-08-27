from __future__ import annotations

"""Command line utilities for RAZAR agents."""

import argparse
import time
from pathlib import Path
from typing import Iterator

from memory import narrative_engine

ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = ROOT / "logs" / "nazarick_story.log"


def _tail_log(path: Path) -> Iterator[str]:
    """Yield appended lines from ``path``."""

    with path.open("r", encoding="utf-8") as fh:
        fh.seek(0, 2)
        while True:
            line = fh.readline()
            if not line:
                time.sleep(0.5)
                continue
            yield line.rstrip("\n")


def _cmd_narrative(_: argparse.Namespace) -> None:
    """Print narratives from the log file or memory."""

    try:
        if LOG_PATH.exists():
            for line in _tail_log(LOG_PATH):
                print(line)
        else:
            for story in narrative_engine.stream_stories():
                print(story)
    except KeyboardInterrupt:  # pragma: no cover - user abort
        pass


def build_parser() -> argparse.ArgumentParser:
    """Create the top level argument parser."""

    parser = argparse.ArgumentParser(prog="razar", description="RAZAR utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    narr_p = sub.add_parser("narrative", help="Stream narrative stories")
    narr_p.set_defaults(func=_cmd_narrative)

    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ``razar`` CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)
    func = args.func
    func(args)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
