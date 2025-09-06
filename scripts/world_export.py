"""Export current world configuration and patch metadata."""

from __future__ import annotations

import argparse

from worlds.config_registry import export_config_file


def main(argv: list[str] | None = None) -> None:
    """Write world configuration to ``path`` (default ``world.json``)."""
    parser = argparse.ArgumentParser(description="Export world configuration")
    parser.add_argument(
        "path",
        nargs="?",
        default="world.json",
        help="Destination file for the exported configuration",
    )
    parser.add_argument(
        "--world",
        help="Name of the world to export (default: WORLD_NAME env or 'default')",
    )
    args = parser.parse_args(argv)
    out_path = export_config_file(args.path, world=args.world)
    print(f"Exported configuration to {out_path}")


if __name__ == "__main__":  # pragma: no cover
    main()
