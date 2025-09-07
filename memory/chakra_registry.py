"""Chakra-aware registry built on top of :mod:`vector_memory`.

Each record is tagged with ``chakra``, ``timestamp`` and ``source`` metadata so
agents can filter memories along energetic dimensions. Optionally integrates
with :mod:`distributed_memory` for off-box persistence when a Redis url is
provided.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

try:  # pragma: no cover - optional dependency
    import vector_memory
except Exception:  # pragma: no cover - optional dependency
    vector_memory = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from distributed_memory import DistributedMemory
except Exception:  # pragma: no cover - optional dependency
    DistributedMemory = None  # type: ignore[assignment]


class ChakraRegistry:
    """Persist and query chakra-tagged events."""

    def __init__(
        self,
        *,
        db_path: str | None = None,
        redis_url: str | None = None,
        redis_client: Any | None = None,
    ) -> None:
        if vector_memory is None:  # pragma: no cover - safeguard
            raise RuntimeError("vector_memory module not available")
        self._dist: Any | None = None
        if redis_url or redis_client:
            if DistributedMemory is None:  # pragma: no cover - safeguard
                raise RuntimeError("distributed_memory module not available")
            self._dist = DistributedMemory(
                url=redis_url or "redis://localhost:6379/0", client=redis_client
            )
            vector_memory.configure(db_path=db_path, redis_client=self._dist.client)
        else:
            vector_memory.configure(db_path=db_path)

    # ------------------------------------------------------------------
    def record(self, chakra: str, text: str, source: str, **metadata: Any) -> None:
        """Store ``text`` with chakra and source information."""

        if vector_memory is None:  # pragma: no cover - safeguard
            return
        meta: Dict[str, Any] = {
            "chakra": chakra,
            "timestamp": datetime.utcnow().isoformat(),
            "source": source,
        }
        meta.update(metadata)
        vector_memory.add_vector(text, meta)

    # ------------------------------------------------------------------
    def search(
        self,
        chakra: str,
        query: str,
        *,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        scoring: str = "hybrid",
    ) -> List[Dict[str, Any]]:
        """Search for events within a chakra matching ``query``."""

        if vector_memory is None:  # pragma: no cover - safeguard
            return []
        meta_filter = dict(filter or {})
        meta_filter["chakra"] = chakra
        return vector_memory.search(query, filter=meta_filter, k=k, scoring=scoring)


__all__ = ["ChakraRegistry"]
