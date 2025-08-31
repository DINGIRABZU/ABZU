from __future__ import annotations

__version__ = "0.2.2"

"""Lifecycle message bus for RAZAR components.

This module uses Redis pub/sub channels to broadcast component status updates
and listen for issue reports.  It exposes a small API used by operational
scripts and command line utilities.
"""

from dataclasses import dataclass
import json
from typing import Dict, Iterator

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    redis = None  # type: ignore

STATUS_KEY = "razar:status"
STATUS_CHANNEL = "razar:status"
ISSUE_CHANNEL = "razar:issues"
CONTROL_CHANNEL = "razar:control"


@dataclass
class Issue:
    """Represents an issue reported by a component."""

    component: str
    issue: str


class LifecycleBus:
    """Redis-backed lifecycle bus.

    Parameters
    ----------
    url:
        Redis connection URL. Defaults to ``redis://localhost:6379/0``.
    """

    def __init__(self, url: str = "redis://localhost:6379/0") -> None:
        if redis is None:  # pragma: no cover - defensive
            raise RuntimeError("redis package is required for LifecycleBus")
        self.url = url
        self._client = redis.Redis.from_url(url)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Status helpers
    def publish_status(self, component: str, status: str) -> None:
        """Broadcast ``status`` for ``component`` and store it in Redis."""
        payload = {"component": component, "status": status}
        data = json.dumps(payload)
        self._client.hset(STATUS_KEY, component, status)
        self._client.publish(STATUS_CHANNEL, data)

    def get_statuses(self) -> Dict[str, str]:
        """Return a mapping of component names to their last known status."""
        raw = self._client.hgetall(STATUS_KEY)
        return {k.decode(): v.decode() for k, v in raw.items()}

    # ------------------------------------------------------------------
    # Control helpers
    def send_control(self, component: str, action: str) -> None:
        """Publish a control message for ``component`` with ``action``."""
        payload = {"component": component, "action": action}
        self._client.publish(CONTROL_CHANNEL, json.dumps(payload))

    # ------------------------------------------------------------------
    # Issue helpers
    def report_issue(self, component: str, issue: str) -> None:
        """Publish an issue notification for ``component``."""
        payload = {"component": component, "issue": issue}
        self._client.publish(ISSUE_CHANNEL, json.dumps(payload))

    def listen_for_issues(self) -> Iterator[Issue]:
        """Yield :class:`Issue` objects as they are reported.

        This is a blocking generator which listens on the ``ISSUE_CHANNEL``
        and yields issues as they arrive.
        """
        pubsub = self._client.pubsub()
        pubsub.subscribe(ISSUE_CHANNEL)
        for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            try:
                data = json.loads(message["data"])
                yield Issue(
                    component=data.get("component", ""),
                    issue=data.get("issue", ""),
                )
            except json.JSONDecodeError:  # pragma: no cover - ignore bad msgs
                continue
