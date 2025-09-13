"""Thin wrapper around the Rust-based crown router."""

from neoabzu_crown import (
    route_query,
    route_decision,
    route_inevitability,
    query_memory,
)

__all__ = [
    "route_query",
    "route_decision",
    "route_inevitability",
    "query_memory",
]
