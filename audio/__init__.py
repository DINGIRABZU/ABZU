"""Compatibility wrapper exposing the :mod:`src.audio` package at top level."""

from __future__ import annotations

import sys as _sys
from importlib import import_module

_audio = import_module("src.audio")
_sys.modules[__name__] = _audio
