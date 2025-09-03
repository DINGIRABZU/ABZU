"""Utility constants shared across RAZAR bootstrap modules."""

from __future__ import annotations

from pathlib import Path

# Base directory for runtime logs
LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"

# Frequently used log file locations
STATE_FILE = LOGS_DIR / "razar_state.json"
HISTORY_FILE = LOGS_DIR / "razar_boot_history.json"
PATCH_LOG_PATH = LOGS_DIR / "razar_ai_patches.json"

# Keep a limited number of mission brief archives for auditability
MAX_MISSION_BRIEFS = 20

__all__ = [
    "LOGS_DIR",
    "STATE_FILE",
    "HISTORY_FILE",
    "PATCH_LOG_PATH",
    "MAX_MISSION_BRIEFS",
]
