"""Intent parser that maps symbolic input to Spiral OS actions."""

from __future__ import annotations

import types
from typing import Any, Callable, Dict, List

try:  # pragma: no cover - fallback when optional modules are missing
    from INANNA_AI import corpus_memory, voice_layer_albedo
except Exception:  # pragma: no cover
    corpus_memory = types.SimpleNamespace(search_corpus=lambda *a, **k: [])
    voice_layer_albedo = types.SimpleNamespace(speak=lambda *a, **k: "")

try:  # pragma: no cover
    import seven_dimensional_music as _sdm  # type: ignore

    if hasattr(_sdm, "play_sequence"):
        seven_dimensional_music = _sdm
    else:  # pragma: no cover - ensure attribute exists for monkeypatching
        seven_dimensional_music = types.SimpleNamespace(
            play_sequence=lambda *a, **k: ""
        )
except Exception:  # pragma: no cover
    seven_dimensional_music = types.SimpleNamespace(play_sequence=lambda *a, **k: "")

try:  # pragma: no cover
    import ritual_trainer as ritual  # type: ignore
except Exception:  # pragma: no cover
    ritual = types.SimpleNamespace(vault_open=lambda *a, **k: {"status": "unhandled"})


# Mapping of intent phrases to action names. The mapping is intentionally
# minimal; tests exercise only a small subset of behaviours.
_INTENTS: Dict[str, Dict[str, Any]] = {
    "summon memory": {"action": "memory.recall"},
    "weave sound": {"action": "voice_layer.play"},
    "open portal": {"action": "gateway.open"},
}


# Action dispatch table – values are callables taking the intent data.
_ACTIONS: Dict[str, Callable[[Dict[str, Any]], Any]] = {
    "memory.recall": lambda d: corpus_memory.search_corpus(d.get("text", "")),
    "voice_layer.play": lambda d: voice_layer_albedo.speak(
        d.get("text", ""), d.get("tone", "neutral")
    ),
    "music.play_sequence": lambda d: seven_dimensional_music.play_sequence(
        d.get("text", ""), d.get("tone", "neutral")
    ),
    "ritual.vault_open": lambda d: ritual.vault_open(d),
    # Placeholder used in tests; patched by callers when needed.
    "gateway.open": lambda d: {"status": "unhandled"},
}


def _gather_text(data: Dict[str, Any]) -> str:
    """Collect text fields from ``data`` for keyword matching."""
    parts: List[str] = []
    text = data.get("text")
    if isinstance(text, str):
        parts.append(text)
    symbols = data.get("symbols")
    if isinstance(symbols, list):
        parts.extend(str(s) for s in symbols)
    return " ".join(parts)


def parse_intent(data: Dict[str, Any]) -> List[Any]:
    """Parse ``data`` and execute matching actions."""
    lowered = _gather_text(data).lower()
    results: List[Any] = []
    for name, info in _INTENTS.items():
        triggers = [name] + info.get("synonyms", []) + info.get("glyphs", [])
        if any(t.lower() in lowered for t in triggers):
            action = info.get("action")
            func = _ACTIONS.get(action) if isinstance(action, str) else None
            if func:
                results.append(func(data))
    return results


def route_intent(intent: Dict[str, Any]) -> Any:
    """Route ``intent`` using the action table."""
    action = intent.get("action")
    func = _ACTIONS.get(action) if isinstance(action, str) else None
    if func:
        return func(intent)
    return {"status": "unhandled"}


__all__ = [
    "parse_intent",
    "route_intent",
    "_INTENTS",
    "_ACTIONS",
    "_gather_text",
    "corpus_memory",
    "voice_layer_albedo",
    "seven_dimensional_music",
    "ritual",
]
