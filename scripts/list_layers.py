#!/usr/bin/env python3
"""Print configured personality layers and whether they are enabled."""
from __future__ import annotations

from pathlib import Path

import yaml

CONFIG_PATH = (
    Path(__file__).resolve().parent.parent / "config" / "settings" / "layers.yaml"
)


def main() -> None:
    if not CONFIG_PATH.exists():
        print("No layer configuration found.")
        return
    data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    layers = data.get("layers", {})
    for name, enabled in sorted(layers.items()):
        status = "enabled" if enabled else "disabled"
        print(f"{name}: {status}")


if __name__ == "__main__":
    main()
