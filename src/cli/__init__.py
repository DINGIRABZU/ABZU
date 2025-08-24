"""Command-line interface utilities.

Expose the main entry points used by the packaging configuration so they can
be referenced as console scripts.
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from .console_interface import run_repl
from .spiral_cortex_terminal import main as spiral_cortex_main
from .voice import main as voice_main


def main(argv: list[str] | None = None) -> None:
    """Entry point for the consolidated ``abzu`` CLI."""
    path = Path(__file__).resolve().parents[1] / "cli.py"
    spec = spec_from_file_location("_abzu_cli", path)
    module = module_from_spec(spec)
    assert spec.loader is not None  # for ``mypy`` and ``pyright``
    spec.loader.exec_module(module)
    module.main(argv)


__all__ = ["run_repl", "spiral_cortex_main", "voice_main", "main"]
