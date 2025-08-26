"""Boot diagnostics for verifying essential services."""

from __future__ import annotations

import importlib
import logging
from types import ModuleType
from typing import Dict, Optional

from .essential_services import VITAL_MODULES

logger = logging.getLogger(__name__)


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
        except ImportError as exc:  # module missing
            logger.error("Missing module %s: %s", name, exc)
            results[name] = None
        except RuntimeError as exc:  # initialization failed
            logger.critical("Runtime failure in %s: %s", name, exc)
            results[name] = None
    return results

__all__ = ["run_boot_checks"]
