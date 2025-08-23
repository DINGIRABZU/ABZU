"""Minimal stub of the `huggingface_hub` package used in tests.

The real `huggingface_hub` dependency is fairly heavy and unnecessary for the
unit tests in this repository. This stub provides the small surface area that
is required by the codebase: the :func:`snapshot_download` function and the
:class:`HfHubHTTPError` exception. Both implementations are no-ops.
"""

from __future__ import annotations


def snapshot_download(*args, **kwargs):
    """Return an empty string without performing any download."""
    return ""


class HfHubHTTPError(Exception):
    """Placeholder exception matching the real library's error type."""
