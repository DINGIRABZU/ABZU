"""CLI utilities for exporting and importing world configuration."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config_registry import export_config_file, import_config_file


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="world", description="World configuration utilities"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_export = sub.add_parser("export", help="Export world configuration")
    p_export.add_argument(
        "path", nargs="?", default="world.json", help="Destination file"
    )
    p_export.add_argument(
        "--world", help="World name (default: WORLD_NAME env or 'default')"
    )

    p_import = sub.add_parser("import", help="Import world configuration")
    p_import.add_argument("path", help="Source file")
    p_import.add_argument(
        "--world", help="World name (default: WORLD_NAME env or 'default')"
    )

    args = parser.parse_args(argv)
    if args.command == "export":
        out_path = export_config_file(args.path, world=args.world)
        print(f"Exported configuration to {Path(out_path)}")
    else:
        import_config_file(args.path, world=args.world)
        print(f"Imported configuration from {args.path}")


if __name__ == "__main__":  # pragma: no cover
    main()
