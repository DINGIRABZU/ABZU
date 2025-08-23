"""Compatibility wrapper exposing the :mod:`src.core` package at top level.

The project uses a ``src`` layout but many modules – especially tests – import
:mod:`core` directly from the repository root.  Providing this small shim keeps
imports working without requiring callers to modify ``sys.path``.
"""

from __future__ import annotations

import sys as _sys
from importlib import import_module

_core = import_module("src.core")
_sys.modules[__name__] = _core
