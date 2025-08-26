"""Command line demo for Albedo persona interactions."""

from __future__ import annotations

import argparse

from agents.albedo.messaging import compose_message_nazarick, compose_message_rival
from agents.albedo.trust import update_trust


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate Albedo dialogue")
    parser.add_argument("entity", help="Entity name to interact with")
    parser.add_argument(
        "outcome",
        choices=["positive", "negative", "neutral", "success", "failure"],
        help="Interaction outcome",
    )
    parser.add_argument(
        "--rival",
        action="store_true",
        help="Treat entity as a rival instead of an ally",
    )
    args = parser.parse_args()

    magnitude, state = update_trust(args.entity, args.outcome)
    if args.rival:
        message = compose_message_rival(args.entity, state, magnitude)
    else:
        message = compose_message_nazarick(args.entity, state, magnitude)
    print(message)


if __name__ == "__main__":  # pragma: no cover - manual demo
    main()
