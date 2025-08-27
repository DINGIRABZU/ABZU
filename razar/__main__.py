from __future__ import annotations

"""Command line utilities for operating the RAZAR lifecycle bus."""

import argparse

from agents.razar.lifecycle_bus import LifecycleBus


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

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:  # pragma: no cover - show help when no subcommand
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover - module CLI
    main()
