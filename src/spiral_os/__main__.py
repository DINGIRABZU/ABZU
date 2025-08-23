"""Command-line interface for Spiral OS utilities."""

from __future__ import annotations

import argparse
import logging
import subprocess
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def deploy_pipeline(path: str | Path) -> None:
    """Execute each step listed in a pipeline YAML file."""
    path = Path(path)
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as exc:
        logger.error("Failed to parse pipeline YAML %s: %s", path, exc)
        raise

    steps = data.get("steps")
    if not isinstance(steps, list):
        raise ValueError("Pipeline YAML must contain a top-level 'steps' list")

    for step in steps:
        command = step if isinstance(step, str) else step.get("run")
        if command:
            try:
                subprocess.run(command, shell=True, check=True)
            except subprocess.CalledProcessError as exc:
                logger.error(
                    "Command failed with exit code %s: %s", exc.returncode, command
                )
                raise


def start_os(args: list[str]) -> None:
    """Launch the ``start_spiral_os`` sequence with forwarded arguments."""
    from . import start_spiral_os as start_module

    start_module.main(args)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``spiral-os`` command line interface."""
    parser = argparse.ArgumentParser(prog="spiral-os")
    subparsers = parser.add_subparsers(dest="command")

    pipeline_parser = subparsers.add_parser("pipeline", help="Pipeline operations")
    pipeline_sub = pipeline_parser.add_subparsers(dest="pipeline_cmd")
    deploy_parser = pipeline_sub.add_parser("deploy", help="Run steps from a YAML file")
    deploy_parser.add_argument("yaml", type=Path, help="Path to pipeline YAML file")

    start_parser = subparsers.add_parser(
        "start", help="Run the start_spiral_os initialization sequence"
    )
    start_parser.add_argument(
        "args", nargs=argparse.REMAINDER, help="Arguments forwarded to start_spiral_os"
    )

    args = parser.parse_args(argv)

    if args.command == "pipeline" and args.pipeline_cmd == "deploy":
        deploy_pipeline(args.yaml)
        return 0
    if args.command == "start":
        start_os(args.args)
        return 0

    parser.print_usage()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
