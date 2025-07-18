from __future__ import annotations

"""Permission checks and rollback helpers for OS Guardian actions."""

import logging
import os
from pathlib import Path
from typing import Callable, Iterable, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Allowlist values may be populated via environment variables
_DEFAULT_COMMANDS = {"echo", "ls", "pwd", "cat"}
_ALLOWED_COMMANDS = set(filter(None, os.environ.get("OG_ALLOWED_COMMANDS", "").split(os.pathsep)))
if not _ALLOWED_COMMANDS:
    _ALLOWED_COMMANDS = set(_DEFAULT_COMMANDS)

_ALLOWED_APPS = set(filter(None, os.environ.get("OG_ALLOWED_APPS", "").split(os.pathsep)))
_ALLOWED_DOMAINS = set(filter(None, os.environ.get("OG_ALLOWED_DOMAINS", "").split(os.pathsep)))

_POLICY = os.environ.get("OG_POLICY", "allow").lower()  # allow, ask or deny

# Simple stack of undo callbacks
_UNDO_STACK: List[Callable[[], None]] = []


def command_allowed(cmd: str) -> bool:
    """Return ``True`` if shell command ``cmd`` is permitted."""
    return cmd in _ALLOWED_COMMANDS


def app_allowed(path: str | Path) -> bool:
    """Return ``True`` if application ``path`` is permitted."""
    name = Path(path).name
    return not _ALLOWED_APPS or name in _ALLOWED_APPS or str(path) in _ALLOWED_APPS


def domain_allowed(url: str) -> bool:
    """Return ``True`` if ``url`` is within an allowed domain."""
    host = urlparse(url).hostname or ""
    return not _ALLOWED_DOMAINS or host in _ALLOWED_DOMAINS


def confirm(prompt: str) -> bool:
    """Return ``True`` if the action should proceed based on ``_POLICY``."""
    if _POLICY == "allow":
        return True
    if _POLICY == "deny":
        logger.warning("Denied: %s", prompt)
        return False
    try:
        answer = input(f"{prompt} [y/N]: ").strip().lower()
    except EOFError:
        return False
    return answer in {"y", "yes"}


def register_undo(func: Callable[[], None]) -> None:
    """Register ``func`` to undo a completed action."""
    _UNDO_STACK.append(func)


def undo_last() -> None:
    """Undo the most recent reversible action."""
    if _UNDO_STACK:
        undo = _UNDO_STACK.pop()
        try:
            undo()
        except Exception as exc:  # pragma: no cover - undo failure is best effort
            logger.error("Failed to undo action: %s", exc)


def undo_all() -> None:
    """Undo all registered actions in reverse order."""
    while _UNDO_STACK:
        undo_last()


__all__ = [
    "command_allowed",
    "app_allowed",
    "domain_allowed",
    "confirm",
    "register_undo",
    "undo_last",
    "undo_all",
]
