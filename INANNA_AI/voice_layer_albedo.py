"""Voice modulation layer with alchemical tone presets."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from . import speaking_engine, voice_evolution

# Tone presets mapping to speed and pitch adjustments
TONE_PRESETS: Dict[str, Dict[str, float]] = {
    "albedo": {"speed": 1.05, "pitch": 0.2},
    "nigredo": {"speed": 0.9, "pitch": -0.3},
    "rubedo": {"speed": 1.1, "pitch": 0.5},
    "lunar": {"speed": 0.95, "pitch": -0.4},
}

try:  # pragma: no cover - optional dependency used during calibration
    import yaml
except Exception:  # pragma: no cover - fallback when PyYAML missing
    yaml = None  # type: ignore


def _load_crown_presets() -> (
    tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, Any]]]
):
    """Return telemetry-derived overrides and their source metadata."""

    if yaml is None:
        return {}, {}

    preset_path = (
        Path(__file__).resolve().parents[1]
        / "crown_config"
        / "settings"
        / "modulation_presets.yaml"
    )
    if not preset_path.exists():
        return {}, {}

    try:
        data: Dict[str, Any] = (
            yaml.safe_load(preset_path.read_text(encoding="utf-8")) or {}
        )
    except Exception:  # pragma: no cover - defensive guard for malformed YAML
        return {}, {}

    tones = data.get("tones", {})
    presets: Dict[str, Dict[str, float]] = {}
    metadata: Dict[str, Dict[str, Any]] = {}
    for name, info in tones.items():
        tone_name = str(name).lower()
        speed = float(
            info.get("speed", TONE_PRESETS.get(tone_name, {}).get("speed", 1.0))
        )
        pitch = float(
            info.get("pitch", TONE_PRESETS.get(tone_name, {}).get("pitch", 0.0))
        )
        presets[tone_name] = {"speed": speed, "pitch": pitch}
        metadata[tone_name] = dict(info)
    return presets, metadata


CROWN_PRESET_METADATA: Dict[str, Dict[str, Any]] = {}

# Inject telemetry-derived preset values before merging configuration overlays.
_crown_overrides, _crown_metadata = _load_crown_presets()
if _crown_overrides:
    TONE_PRESETS.update(_crown_overrides)
    CROWN_PRESET_METADATA.update(_crown_metadata)

# Merge presets defined in ``voice_config.yaml``
for info in voice_evolution.VOICE_CONFIG.values():
    tone = info.get("tone")
    if tone:
        TONE_PRESETS.setdefault(
            tone.lower(),
            {
                "speed": float(info.get("speed", 1.0)),
                "pitch": float(info.get("pitch", 0.0)),
            },
        )


def _ensure_preset(tone: str, preset: Dict[str, float] | None = None) -> None:
    """Inject preset ``tone`` into the voice evolution styles."""
    preset = preset or TONE_PRESETS.get(tone)
    if not preset:
        return
    voice_evolution.DEFAULT_VOICE_STYLES[tone] = preset
    voice_evolution._evolver.styles[tone] = preset


# Load presets when this module is imported
for _name, _preset in TONE_PRESETS.items():
    _ensure_preset(_name, _preset)


def modulate_voice(text: str, tone: str) -> str:
    """Synthesize ``text`` using the style defined by ``tone``."""
    tone_key = tone.lower()
    cfg = voice_evolution.VOICE_CONFIG.get(tone_key)
    if cfg:
        style = {
            "speed": float(cfg.get("speed", 1.0)),
            "pitch": float(cfg.get("pitch", 0.0)),
        }
        style_name = cfg.get("tone", tone_key).lower()
        _ensure_preset(style_name, style)
        return speaking_engine.synthesize_speech(text, style_name)

    _ensure_preset(tone_key)
    return speaking_engine.synthesize_speech(text, tone_key)


def speak(text: str, tone: str) -> str:
    """Synthesize and immediately play ``text`` with ``tone``."""
    path = modulate_voice(text, tone)
    speaking_engine.play_wav(path)
    return path


__all__ = ["modulate_voice", "speak", "TONE_PRESETS", "CROWN_PRESET_METADATA"]
