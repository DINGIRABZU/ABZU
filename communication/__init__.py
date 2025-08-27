"""Communication utilities and microservices."""

from __future__ import annotations

from .command_dispatch import app as command_dispatch_app, register_agent

__all__ = ["command_dispatch_app", "register_agent"]
