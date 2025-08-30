"""Validate API schemas against the FastAPI application."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType

from openapi_spec_validator import validate_spec
import jsonschema

__version__ = "0.1.0"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class DummyVC:
    """Stub voice cloner used for schema validation."""

    def capture_sample(self, *a, **k) -> None:
        """Stub capture."""
        return None

    def synthesize(self, *a, **k):
        """Stub synthesize."""
        return b"", 0.0


voice_cloner_mod = ModuleType("voice_cloner")
voice_cloner_mod.VoiceCloner = DummyVC
audio_mod = ModuleType("audio")
audio_mod.voice_cloner = voice_cloner_mod
sys.modules.setdefault("audio", audio_mod)
sys.modules.setdefault("audio.voice_cloner", voice_cloner_mod)

style_library_mod = ModuleType("style_library")
style_library_mod.STYLES_DIR = Path(".")
style_engine_mod = ModuleType("style_engine")
style_engine_mod.style_library = style_library_mod
sys.modules.setdefault("style_engine", style_engine_mod)
sys.modules.setdefault("style_engine.style_library", style_library_mod)

from src.api.server import app

spec = app.openapi()
validate_spec(spec)

with open("docs/schemas/openapi.json", "r", encoding="utf-8") as fh:
    committed = json.load(fh)

if spec != committed:
    raise SystemExit("Committed OpenAPI spec is out of sync with application")

with open(
    "docs/schemas/stream_avatar_message.schema.json", "r", encoding="utf-8"
) as fh:
    jsonschema.Draft7Validator.check_schema(json.load(fh))

print("Schemas validated against running API")
