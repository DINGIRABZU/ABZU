from __future__ import annotations

"""Command line interface for OS Guardian."""

import argparse

from . import action_engine, planning


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ``os_guardian`` CLI."""
    parser = argparse.ArgumentParser(prog="os-guardian")
    sub = parser.add_subparsers(dest="cmd", required=True)

    open_p = sub.add_parser("open_app", help="Launch an application")
    open_p.add_argument("path")

    click_p = sub.add_parser("click", help="Click coordinates")
    click_p.add_argument("x", type=int)
    click_p.add_argument("y", type=int)

    type_p = sub.add_parser("type", help="Type text")
    type_p.add_argument("text")

    plan_p = sub.add_parser("plan", help="Plan a command")
    plan_p.add_argument("command")

    args = parser.parse_args(argv)

    if args.cmd == "open_app":
        action_engine.open_app(args.path)
    elif args.cmd == "click":
        action_engine.click(args.x, args.y)
    elif args.cmd == "type":
        action_engine.type_text(args.text)
    elif args.cmd == "plan":
        steps = planning.plan(args.command)
        for step in steps:
            print(step)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
