#!/usr/bin/env python3
"""Utility script to print a cuneiform greeting before serving the page."""


def print_banner() -> None:
    """Print the cuneiform welcome banner."""
    banner = (
        "\U0001202D\U00012129\U00012306 "
        "\U00012120\U0001208A "
        "\U0001213F\U0001213E\U00012100"
    )
    print(banner)


if __name__ == "__main__":
    print_banner()
