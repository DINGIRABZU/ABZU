# Patent pending – see PATENTS.md
"""Python wrapper for the Rust crown router."""

__version__ = "0.1.1"

from neoabzu_crown import route_decision, route_query

__all__ = ["route_decision", "route_query"]
