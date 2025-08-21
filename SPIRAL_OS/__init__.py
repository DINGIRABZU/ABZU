from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from . import qnl_engine, symbolic_parser

# Expose modules from repository root so tests can import `SPIRAL_OS.seven_dimensional_music`.
_repo_root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "seven_dimensional_music", _repo_root / "seven_dimensional_music.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)  # type: ignore
sys.modules["SPIRAL_OS.seven_dimensional_music"] = module

__all__ = ["qnl_engine", "symbolic_parser", "seven_dimensional_music"]
