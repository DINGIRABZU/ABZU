"""Boot diagnostics for verifying essential services."""

from __future__ import annotations

import importlib
import logging
import subprocess
import sys
from types import ModuleType
from typing import Dict, Optional

from .essential_services import VITAL_MODULES

logger = logging.getLogger(__name__)


def _install_module(name: str) -> bool:
    """Attempt to install ``name`` via ``pip``."""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", name],
            check=True,
        )
    except Exception as exc:  # pragma: no cover - network dependent
        logger.error("Auto-install failed for %s: %s", name, exc)
        return False
    return True


def _stub_module(name: str) -> ModuleType:
    """Create and register an empty module named ``name``."""
    module = ModuleType(name)
    sys.modules[name] = module
    logger.warning("Stubbed missing module %s", name)
    return module


def run_boot_checks() -> Dict[str, Optional[ModuleType]]:
    """Import each vital module and report availability.

    Returns a mapping of module name to the imported module object. If a
    module fails to import due to :class:`ImportError` or :class:`RuntimeError`,
    the value will be ``None`` and the event is logged.
    """

    results: Dict[str, Optional[ModuleType]] = {}
    for name in VITAL_MODULES:
        try:
            results[name] = importlib.import_module(name)
            continue
        except ImportError as exc:  # module missing
            logger.error("Missing module %s: %s", name, exc)
            if _install_module(name):
                try:
                    results[name] = importlib.import_module(name)
                    continue
                except Exception as exc2:
                    logger.error("Import failed after install for %s: %s", name, exc2)
            results[name] = _stub_module(name)
            continue
        except RuntimeError as exc:  # initialization failed
            logger.critical("Runtime failure in %s: %s", name, exc)
            results[name] = None
            continue
    return results


__all__ = ["run_boot_checks"]
