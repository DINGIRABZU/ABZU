from __future__ import annotations

"""Utilities for retrieving stories with event context."""

__version__ = "0.1.0"

import json
from typing import Any, Dict, Iterator, Optional

from . import narrative_engine


def find(
    agent_id: Optional[str] = None,
    event_type: Optional[str] = None,
    text: Optional[str] = None,
) -> Iterator[Dict[str, Any]]:
    """Yield joined stories and event metadata.

    Results come from joining ``story_index`` and ``events`` tables. Optional
    filters by ``agent_id``, ``event_type`` and substring ``text`` are applied
    to the narrative text.
    """

    sql = (
        "SELECT s.time, s.agent_id, s.event_type, s.text, e.id, e.payload "
        "FROM story_index AS s JOIN events AS e "
        "ON s.time = e.time AND s.agent_id = e.agent_id "
        "AND s.event_type = e.event_type"
    )
    clauses: list[str] = []
    params: list[Any] = []
    if agent_id:
        clauses.append("s.agent_id = ?")
        params.append(agent_id)
    if event_type:
        clauses.append("s.event_type = ?")
        params.append(event_type)
    if text:
        clauses.append("s.text LIKE ?")
        params.append(f"%{text}%")
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY s.time"
    with narrative_engine._get_conn() as conn:  # type: ignore[attr-defined]
        for ts, ag, et, story_text, event_id, payload in conn.execute(sql, params):
            yield {
                "time": ts,
                "agent_id": ag,
                "event_type": et,
                "text": story_text,
                "event_id": event_id,
                "payload": json.loads(payload),
            }


__all__ = ["find"]
