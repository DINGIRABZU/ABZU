"""Command line utilities for RAZAR agents."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Iterator

from memory import narrative_engine
from agents.nazarick.ethics_manifesto import LAWS
from agents.nazarick.trust_matrix import TrustMatrix
from agents.razar import mission_logger, retro_bootstrap

ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = ROOT / "logs" / "nazarick_story.log"
PATCH_LOG_PATH = ROOT / "logs" / "razar_ai_patches.json"


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


def _cmd_ethics(_: argparse.Namespace) -> None:
    """Print the Nazarick manifesto laws."""
    for idx, law in enumerate(LAWS, 1):
        print(f"{idx}. {law.name}: {law.description}")


def _cmd_trust(args: argparse.Namespace) -> None:
    """Display trust score and protocol for ``args.entity``."""
    matrix = TrustMatrix()
    try:
        info = matrix.evaluate_entity(args.entity)
    finally:
        matrix.close()
    print(f"Trust: {info['trust']}")
    print(f"Protocol: {info['protocol']}")


def _cmd_timeline(_: argparse.Namespace) -> None:
    """Print the event timeline from the mission log."""
    for entry in mission_logger.timeline():
        details = f" - {entry['details']}" if entry.get("details") else ""
        msg = (
            f"{entry['timestamp']} {entry['event']} {entry['component']}: "
            f"{entry['status']}{details}"
        )
        print(msg)


def _cmd_bootstrap(args: argparse.Namespace) -> None:
    """Rebuild modules based on documentation references."""
    if args.from_docs:
        for path in retro_bootstrap.bootstrap_from_docs():
            print(path)


def _cmd_patches(args: argparse.Namespace) -> None:
    """Display or export applied patch records."""
    if not PATCH_LOG_PATH.exists():
        print("No patch records found")
        return
    data = PATCH_LOG_PATH.read_text(encoding="utf-8")
    if args.export:
        Path(args.export).write_text(data, encoding="utf-8")
    else:
        print(data)


def build_parser() -> argparse.ArgumentParser:
    """Create the top level argument parser."""
    parser = argparse.ArgumentParser(prog="razar", description="RAZAR utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    narr_p = sub.add_parser("narrative", help="Stream narrative stories")
    narr_p.set_defaults(func=_cmd_narrative)

    ethics_p = sub.add_parser("ethics", help="Show manifesto laws")
    ethics_p.set_defaults(func=_cmd_ethics)

    trust_p = sub.add_parser("trust", help="Evaluate entity trust")
    trust_p.add_argument("entity", help="Entity name")
    trust_p.set_defaults(func=_cmd_trust)

    timeline_p = sub.add_parser("timeline", help="Reconstruct mission events")
    timeline_p.set_defaults(func=_cmd_timeline)

    bootstrap_p = sub.add_parser("bootstrap", help="Rebuild modules")
    bootstrap_p.add_argument(
        "--from-docs",
        action="store_true",
        help="Reconstruct modules referenced in docs",
    )
    bootstrap_p.set_defaults(func=_cmd_bootstrap)

    patches_p = sub.add_parser("patches", help="Show or export patch records")
    patches_p.add_argument("--export", help="Write records to FILE instead of stdout")
    patches_p.set_defaults(func=_cmd_patches)

    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ``razar`` CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    func = args.func
    func(args)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
