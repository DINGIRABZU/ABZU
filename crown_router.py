from __future__ import annotations

"""Combine model and expression routing for the Crown agent."""

from typing import Any, Dict

import emotional_state
import vector_memory

from orchestrator import MoGEOrchestrator
from crown_decider import decide_expression_options


def route_decision(
    text: str,
    emotion_data: Dict[str, Any],
    orchestrator: MoGEOrchestrator | None = None,
) -> Dict[str, Any]:
    """Return combined routing decision for ``text``.

    The function delegates model selection to :class:`MoGEOrchestrator` and
    chooses expression options based on both the current emotion and recent
    history.  Past ``expression_decision`` records are retrieved from
    :mod:`vector_memory` and weighted higher when their stored ``soul_state``
    matches :func:`emotional_state.get_soul_state`.  These weights influence the
    final ``tts_backend`` and ``avatar_style`` choices in addition to the
    baseline recommendation from :func:`crown_decider.decide_expression_options`.

    Parameters
    ----------
    text:
        User input text.
    emotion_data:
        Parsed emotion information for the input.
    orchestrator:
        Optional existing :class:`MoGEOrchestrator` instance.

    Returns
    -------
    Dict[str, Any]
        Decision containing ``model``, ``tts_backend``, ``avatar_style`` and
        ``aura``.
    """
    orch = orchestrator or MoGEOrchestrator()
    result = orch.route(
        text,
        emotion_data,
        text_modality=False,
        voice_modality=False,
        music_modality=False,
    )

    emotion = emotion_data.get("emotion", "neutral")
    opts = decide_expression_options(emotion)

    soul = emotional_state.get_soul_state()
    try:
        records = vector_memory.search(
            "",
            filter={"type": "expression_decision", "emotion": emotion},
            k=20,
        )
    except Exception:
        records = []

    backend_weights: Dict[str, float] = {opts.get("tts_backend", ""): 1.0}
    avatar_weights: Dict[str, float] = {opts.get("avatar_style", ""): 1.0}
    for rec in records:
        w = 2.0 if soul and rec.get("soul_state") == soul else 1.0
        b = rec.get("tts_backend")
        a = rec.get("avatar_style")
        if b:
            backend_weights[b] = backend_weights.get(b, 0.0) + w
        if a:
            avatar_weights[a] = avatar_weights.get(a, 0.0) + w

    tts_backend = max(backend_weights, key=backend_weights.get)
    avatar_style = max(avatar_weights, key=avatar_weights.get)

    return {
        "model": result.get("model"),
        "tts_backend": tts_backend,
        "avatar_style": avatar_style,
        "aura": opts.get("aura"),
    }


__all__ = ["route_decision"]
