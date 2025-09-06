#!/usr/bin/env python3
"""Display the cuneiform welcome banner and boot the memory bundle."""
from __future__ import annotations

from pathlib import Path

from memory import broadcast_layer_event


def main() -> None:
    banner_path = Path(__file__).with_name("cuneiform_message.txt")
    message = banner_path.read_text(encoding="utf-8")
    print(message)
    broadcast_layer_event({})


if __name__ == "__main__":
    main()
