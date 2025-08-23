"""Common media processing interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MediaProcessor(ABC):
    """Abstract base class for media processors."""

    @abstractmethod
    def process(self, *args: Any, **kwargs: Any) -> Any:
        """Process media and return a result."""
        raise NotImplementedError
