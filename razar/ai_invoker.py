"""High level wrapper for remote RAZAR agents.

This module delegates failure contexts to the configured remote agent and
applies any suggested patches via :mod:`agents.razar.code_repair`.
"""

from __future__ import annotations

__all__ = ["handover"]

import logging
from pathlib import Path
from typing import Any, Dict

from agents.razar import ai_invoker as remote_ai_invoker
from agents.razar import code_repair

__version__ = "0.1.0"

LOGGER = logging.getLogger(__name__)


def handover(
    component: str,
    error: str,
    *,
    context: Dict[str, Any] | None = None,
    config_path: Path | str | None = None,
) -> bool:
    """Delegate ``component`` failure to a remote agent and apply patches.

    Parameters
    ----------
    component:
        Name of the failing component.
    error:
        Error message describing the failure.
    context:
        Optional additional context forwarded to the remote agent.
    config_path:
        Optional override for the remote agent configuration file.

    Returns
    -------
    bool
        ``True`` if at least one patch was applied successfully, otherwise
        ``False``.
    """
    ctx: Dict[str, Any] = {"component": component, "error": error}
    if context:
        ctx.update(context)
    try:
        suggestion = remote_ai_invoker.handover(context=ctx, config_path=config_path)
    except Exception:  # pragma: no cover - defensive
        LOGGER.exception("Remote agent invocation failed for %s", component)
        return False
    if not suggestion:
        return False
    patches = suggestion if isinstance(suggestion, list) else [suggestion]
    applied = False
    for patch in patches:
        module = patch.get("module")
        if not module:
            continue
        tests = [Path(p) for p in patch.get("tests", [])]
        err = patch.get("error", error)
        try:
            if code_repair.repair_module(Path(module), tests, err):
                applied = True
        except Exception:  # pragma: no cover - defensive
            LOGGER.exception("Failed to apply patch for %s", module)
    return applied
