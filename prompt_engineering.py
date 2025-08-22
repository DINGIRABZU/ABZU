from __future__ import annotations

"""Prompt transformations based on style presets."""

from typing import Dict

from style_engine.style_library import load_style_config

_PRESETS: Dict[str, str] = {
    "ltx": "Render with LTX flair: {prompt}",
    "pusa_v1": "Channeling PUSA V1 vibe: {prompt}",
}


def apply_style_preset(
    prompt: str, style: str, presets: Dict[str, str] | None = None
) -> str:
    """Apply a style preset to ``prompt``.

    Parameters
    ----------
    prompt:
        Base user prompt.
    style:
        Name of the style preset defined in ``style_engine/styles``.
    presets:
        Optional mapping of processor name to template string containing
        ``{prompt}`` placeholder.

    Returns
    -------
    str
        Transformed prompt with style instructions.
    """
    config = load_style_config(style)
    mapping = presets or _PRESETS
    template = mapping.get(config.processor)
    if not template:
        return prompt
    return template.format(prompt=prompt)
