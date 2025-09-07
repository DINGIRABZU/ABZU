from __future__ import annotations

import sys
import types
from pathlib import Path

otel = types.ModuleType("opentelemetry")
otel.trace = types.SimpleNamespace(get_tracer=lambda *a, **k: None)
sys.modules.setdefault("opentelemetry", otel)

from agents.nazarick.document_registry import DocumentRegistry


def test_registry_scans_and_emits_versions(tmp_path):
    registry = DocumentRegistry()
    docs = list(registry.iter_documents())
    names = {Path(d.path).name: d for d in docs}
    # expected canonical files
    assert "GENESIS_.md" in names
    assert "EA_ENUMA_ELISH_.md" in names

    info = names["EA_ENUMA_ELISH_.md"]
    assert info.version
    assert len(info.checksum) == 64
    assert info.last_updated

    out = tmp_path / "index.md"
    registry.generate_index(out)
    text = out.read_text()
    assert "EA_ENUMA_ELISH_.md" in text
    assert info.version in text
