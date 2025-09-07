from __future__ import annotations

"""Utilities for formatting outbound connector messages.

Each formatted message is serialized as JSON and includes three metadata
fields in addition to the original ``content``:

``chakra``
    The chakra tag identifying the message origin.
``version``
    Version string for the formatter. Can be overridden when calling
    :func:`format_message`.
``recovery_url``
    URL pointing to recovery instructions. Defaults to the value of the
    ``RECOVERY_URL`` environment variable or a placeholder.
"""

import json
import os
from typing import Any, Dict

__all__ = ["format_message"]

__version__ = "0.1.0"

_DEFAULT_RECOVERY_URL = os.getenv("RECOVERY_URL", "https://status.abzu.ai/recover")


def format_message(
    chakra: str,
    content: str,
    *,
    version: str | None = None,
    recovery_url: str | None = None,
) -> str:
    """Return ``content`` JSON-encoded with metadata fields.

    Parameters
    ----------
    chakra:
        Chakra tag identifying the message origin.
    content:
        Text content of the message.
    version:
        Optional version string. Defaults to ``__version__``.
    recovery_url:
        Optional recovery URL. Defaults to ``RECOVERY_URL`` environment
        variable or a placeholder value.
    """

    data: Dict[str, Any] = {
        "chakra": chakra,
        "content": content,
        "version": version or __version__,
        "recovery_url": recovery_url or _DEFAULT_RECOVERY_URL,
    }
    return json.dumps(data)
