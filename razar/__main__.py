from __future__ import annotations

"""Command line utilities for operating the RAZAR lifecycle bus."""

import argparse
from pathlib import Path

from agents.razar.ignition_builder import build_ignition
from agents.razar.lifecycle_bus import LifecycleBus
from agents.razar import mission_logger
from agents.razar.blueprint_synthesizer import synthesize


def _cmd_status(args: argparse.Namespace) -> None:
    bus = LifecycleBus(url=args.url)
    statuses = bus.get_statuses()
    if args.component:
        status = statuses.get(args.component, "unknown")
        print(f"{args.component}: {status}")
    else:
        for comp, status in sorted(statuses.items()):
            print(f"{comp}: {status}")


def _cmd_stop(args: argparse.Namespace) -> None:
    bus = LifecycleBus(url=args.url)
    bus.send_control(args.component, "stop")
    print(f"Stop signal sent to {args.component}")


def _cmd_build_ignition(args: argparse.Namespace) -> None:
    build_ignition(Path(args.blueprint), Path(args.output))


def _cmd_timeline(_: argparse.Namespace) -> None:
    """Print the chronological boot history from the mission log."""

    for entry in mission_logger.timeline():
        details = f" - {entry['details']}" if entry.get("details") else ""
        print(
            f"{entry['timestamp']} {entry['event']} {entry['component']}: {entry['status']}{details}"
        )


def _cmd_map(_: argparse.Namespace) -> None:
    """Build and display the component dependency graph."""

    graph = synthesize()
    try:
        for node in sorted(graph.nodes):
            targets = sorted(Path(t).name for _, t in graph.out_edges(node))
            name = Path(node).name
            if targets:
                deps = ", ".join(targets)
                print(f"{name}: {deps}")
            else:
                print(f"{name}: (no links)")
    except BrokenPipeError:  # pragma: no cover - stream closed by pipe
        pass


def main() -> None:  # pragma: no cover - CLI entry point
    parser = argparse.ArgumentParser(description="RAZAR lifecycle utilities")
    parser.add_argument(
        "--url",
        default="redis://localhost:6379/0",
        help="Redis connection URL",
    )
    sub = parser.add_subparsers(dest="command")

    p_status = sub.add_parser("status", help="Show component status")
    p_status.add_argument("component", nargs="?", help="Component to query")
    p_status.set_defaults(func=_cmd_status)

    p_stop = sub.add_parser("stop", help="Request a component to stop")
    p_stop.add_argument("component", help="Component name")
    p_stop.set_defaults(func=_cmd_stop)

    p_ignition = sub.add_parser(
        "build-ignition", help="Regenerate docs/Ignition.md from the blueprint"
    )
    p_ignition.add_argument(
        "--blueprint",
        default=Path(__file__).resolve().parents[1] / "docs" / "system_blueprint.md",
        help="Path to system_blueprint.md",
    )
    p_ignition.add_argument(
        "--output",
        default=Path(__file__).resolve().parents[1] / "docs" / "Ignition.md",
        help="Output path for Ignition.md",
    )
    p_ignition.set_defaults(func=_cmd_build_ignition)

    p_timeline = sub.add_parser("timeline", help="Show event timeline")
    p_timeline.set_defaults(func=_cmd_timeline)

    p_map = sub.add_parser("map", help="Visualize component relationships")
    p_map.set_defaults(func=_cmd_map)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:  # pragma: no cover - show help when no subcommand
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover - module CLI
    main()
