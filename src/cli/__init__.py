"""Command-line interface utilities.

Expose the main entry points used by the packaging configuration so they can
be referenced as console scripts.
"""

from __future__ import annotations

from .console_interface import run_repl
from .spiral_cortex_terminal import main as spiral_cortex_main
from .voice import main as voice_main

__all__ = ["run_repl", "spiral_cortex_main", "voice_main"]
