"""Lightweight proxy to :mod:`agents.razar.mission_logger`.

Importing ``agents.razar`` triggers a heavy dependency chain that introduces
several circular imports during test collection.  The mission logger itself is
stand‑alone, so this module loads it directly from the ``agents`` package using
``importlib`` and re‑exports it under the ``razar`` namespace.  This keeps the
public API stable while avoiding the import side effects.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# Resolve the actual mission_logger.py file within the agents package without
# importing ``agents.razar`` (which pulls in optional runtime dependencies and
# may create circular imports).
_path = Path(__file__).resolve().parents[1] / "agents" / "razar" / "mission_logger.py"
_spec = importlib.util.spec_from_file_location("agents.razar.mission_logger", _path)
assert _spec and _spec.loader  # pragma: no cover - sanity check
_module = importlib.util.module_from_spec(_spec)
# Register the module under its spec name before execution so decorators like
# ``@dataclass`` can resolve ``sys.modules[__spec__.name]`` during import.
sys.modules[_spec.name] = _module  # type: ignore[index]
_spec.loader.exec_module(_module)

# Expose the loaded module as if ``razar.mission_logger`` were defined here.
sys.modules[__name__] = _module
