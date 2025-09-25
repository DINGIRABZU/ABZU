#!/usr/bin/env python3
"""Verify memory layers respond with ready bootstrap data.

Runs minimal queries against each layer. Raises ``RuntimeError``
if any layer is empty or unavailable, mirroring the ``ready``
state emitted by the Rust bundle. Used to guard Albedo
initialisation before persona modules load. Reports optional
fallback usage so Stage B rehearsals can halt when stubs are
active.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
import sys
import os
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

DATA_DIR = ROOT / "data"
os.environ.setdefault("CORTEX_PATH", str(DATA_DIR / "cortex.jsonl"))
os.environ.setdefault("EMOTION_DB_PATH", str(DATA_DIR / "emotions.db"))
os.environ.setdefault("MENTAL_JSON_PATH", str(DATA_DIR / "tasks.jsonl"))
os.environ.setdefault("SPIRITUAL_DB_PATH", str(DATA_DIR / "ontology.db"))
os.environ.setdefault("NARRATIVE_LOG_PATH", str(DATA_DIR / "story.log"))

__version__ = "0.1.2"

logger = logging.getLogger("memory.layer_check")

from memory.cortex import query_spirals
from memory.emotional import fetch_emotion_history, get_connection as emotion_conn

try:
    from memory.mental import query_related_tasks

    _MENTAL_FALLBACK = False
except Exception:  # mental layer optional
    from memory.optional.mental import query_related_tasks

    _MENTAL_FALLBACK = True
from memory.spiritual import lookup_symbol_history, get_connection as spirit_conn
from memory.narrative_engine import stream_stories
from memory.bundle import MemoryBundle


@dataclass(frozen=True)
class OptionalStubActivation:
    """Structured record describing an optional stub activation."""

    layer: str
    module: str
    reason: str | None


@dataclass(frozen=True)
class MemoryLayerCheckReport:
    """Summary of memory layer readiness and optional fallback usage."""

    statuses: Dict[str, str]
    optional_stubs: List[OptionalStubActivation]
    bundle_implementation: str


def _gather_optional_stubs(bundle: MemoryBundle) -> List[OptionalStubActivation]:
    optional: List[OptionalStubActivation] = []
    for layer, diag in bundle.diagnostics.items():
        loaded_module = diag.get("loaded_module")
        if isinstance(loaded_module, str) and loaded_module.startswith(
            "memory.optional."
        ):
            reason = diag.get("fallback_reason")
            activation = OptionalStubActivation(
                layer=layer,
                module=loaded_module,
                reason=str(reason) if reason is not None else None,
            )
            optional.append(activation)
    return optional


def verify_memory_layers() -> MemoryLayerCheckReport:
    """Ensure each memory layer returns data and report fallback usage."""
    if not query_spirals(tags=["example"]):
        raise RuntimeError("cortex layer empty")

    if not fetch_emotion_history(60, conn=emotion_conn()):
        raise RuntimeError("emotional layer empty")

    if not _MENTAL_FALLBACK and not query_related_tasks("taskA"):
        raise RuntimeError("mental layer empty")

    if not lookup_symbol_history("\u263E", conn=spirit_conn()):
        raise RuntimeError("spiritual layer empty")

    if not list(stream_stories()):
        raise RuntimeError("narrative layer empty")

    bundle = MemoryBundle()
    statuses = bundle.initialize()
    optional = _gather_optional_stubs(bundle)

    for activation in optional:
        logger.warning(
            "Optional memory stub active: layer=%s module=%s reason=%s",
            activation.layer,
            activation.module,
            activation.reason or "unspecified",
        )

    implementation = getattr(bundle, "implementation", "neoabzu_memory")
    return MemoryLayerCheckReport(
        statuses=statuses,
        optional_stubs=optional,
        bundle_implementation=str(implementation),
    )


if __name__ == "__main__":  # pragma: no cover - manual check
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )
    report = verify_memory_layers()
    if report.optional_stubs:
        print(
            "optional stubs detected:",
            ", ".join(f"{item.layer}→{item.module}" for item in report.optional_stubs),
        )
        sys.exit(1)
    print("memory checks passed")
