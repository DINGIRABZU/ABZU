from __future__ import annotations

from pathlib import Path
import importlib.util
import sys

# Expose modules from repository root so tests can import `SPIRAL_OS.xxx`.
_repo_root = Path(__file__).resolve().parents[1]
for name in ["mix_tracks", "seven_dimensional_music"]:
    spec = importlib.util.spec_from_file_location(name, _repo_root / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    sys.modules[f"SPIRAL_OS.{name}"] = module

__all__ = ["mix_tracks", "seven_dimensional_music"]
