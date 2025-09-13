"""Thin wrapper around the Rust-based persona state manager."""

from neoabzu_persona import (
    get_current_layer,
    set_current_layer,
    get_last_emotion,
    set_last_emotion,
    load_persona_profiles,
)

__all__ = [
    "get_current_layer",
    "set_current_layer",
    "get_last_emotion",
    "set_last_emotion",
    "load_persona_profiles",
]
