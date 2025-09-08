#!/usr/bin/env python3
"""Initialize mandatory layers, start Crown, and report readiness."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from agents.nazarick.service_launcher import launch_required_agents
from init_crown_agent import initialize_crown
from memory.bundle import MemoryBundle
from worlds.services import load_manifest, warn_missing_services

__version__ = "0.2.1"


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
    statuses = bundle.initialize()
    for layer, status in statuses.items():
        logging.info("memory %s: %s", layer, status)

    logging.info("Starting Crown services...")
    initialize_crown()

    logging.info("Launching agent profiles...")
    events = launch_required_agents()
    for event in events:
        logging.info("agent %s: %s", event.get("agent"), event.get("status"))

    logging.info("World bootstrap complete")


if __name__ == "__main__":
    main()
