#!/usr/bin/env python3
"""Initialize mandatory layers, start Crown, and report readiness."""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

from scripts._stage_runtime import bootstrap, format_sandbox_summary

ROOT = bootstrap(
    optional_modules=[
        "crown_decider",
        "crown_prompt_orchestrator",
        "emotional_state",
        "servant_model_manager",
        "state_transition_engine",
        "tools.session_logger",
    ]
)

from agents.nazarick.service_launcher import launch_required_agents
from init_crown_agent import initialize_crown
from memory.bundle import MemoryBundle
from worlds.services import load_manifest, warn_missing_services
from monitoring.boot_metrics import (
    MemoryInitMetricValues,
    record_memory_init_metrics,
    summarize_memory_statuses,
)

__version__ = "0.3.0"

LOGGER = logging.getLogger("scripts.bootstrap_world")


def _prepare_file_backed_storage(root: Path) -> None:
    """Ensure file-backed paths exist and environment defaults are set."""
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)

    env_defaults = {
        "CORTEX_BACKEND": "file",
        "CORTEX_PATH": str(data / "cortex_memory_spiral.jsonl"),
        "EMOTION_BACKEND": "file",
        "EMOTION_DB_PATH": str(data / "emotions.db"),
        "MENTAL_BACKEND": "file",
        "MENTAL_JSON_PATH": str(data / "tasks.jsonl"),
        "SPIRIT_BACKEND": "file",
        "SPIRITUAL_DB_PATH": str(data / "ontology.db"),
        "NARRATIVE_BACKEND": "file",
        "NARRATIVE_LOG_PATH": str(data / "story.log"),
    }
    for key, value in env_defaults.items():
        os.environ.setdefault(key, value)


def main() -> None:
    """Bootstrap world services and report their status."""
    logging.basicConfig(level=logging.INFO)
    root = Path(__file__).resolve().parents[1]
    _prepare_file_backed_storage(root)

    manifest = load_manifest(root / "worlds" / "services.yaml")
    world = os.getenv("WORLD_NAME", "default")
    warn_missing_services(manifest, world)

    bundle = MemoryBundle()
    statuses = _initialize_with_metrics(bundle)
    for layer, status in statuses.items():
        logging.info("memory %s: %s", layer, status)

    logging.info("Starting Crown services...")
    initialize_crown()

    logging.info("Launching agent profiles...")
    events = launch_required_agents()
    for event in events:
        logging.info("agent %s: %s", event.get("agent"), event.get("status"))

    logging.info("World bootstrap complete")
    logging.info(format_sandbox_summary("Sandbox status"))


def _initialize_with_metrics(bundle: MemoryBundle) -> dict[str, str]:
    """Initialize the memory bundle while capturing telemetry."""

    start = time.perf_counter()
    statuses: dict[str, str] = {}
    error: Optional[BaseException] = None
    try:
        statuses = bundle.initialize()
        return statuses
    except Exception as exc:  # pragma: no cover - propagate failure to caller
        error = exc
        raise
    finally:
        duration = time.perf_counter() - start
        total, ready, failed = summarize_memory_statuses(statuses)
        log_extra = {
            "memory_init_duration": duration,
            "memory_init_failed": failed,
            "memory_init_ready": ready,
            "memory_init_source": "bootstrap_world",
            "memory_layers": statuses,
        }
        if error is not None:
            LOGGER.error(
                "Memory bundle initialization failed after %.3fs",
                duration,
                exc_info=error,
                extra=log_extra,
            )
        else:
            LOGGER.info(
                "Memory bundle initialization finished in %.3fs "
                "(%s/%s ready, %s failed)",
                duration,
                ready,
                total,
                failed,
                extra=log_extra,
            )
        try:
            record_memory_init_metrics(
                MemoryInitMetricValues(
                    duration_seconds=float(duration),
                    layer_total=float(total),
                    layer_ready=float(ready),
                    layer_failed=float(failed),
                    source="bootstrap_world",
                    error=(error is not None) or failed > 0,
                )
            )
        except Exception:  # pragma: no cover - best-effort metrics export
            LOGGER.debug(
                "Unable to export memory initialization metrics", exc_info=True
            )


if __name__ == "__main__":
    main()
