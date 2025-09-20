#!/usr/bin/env bash
# Install pinned audio dependencies
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

pip install \
  librosa==0.11.0 \
  soundfile==0.13.1 \
  opensmile==2.6.0 \
  clap==0.7 \
  rave==1.0.0

python3 - <<'PY'
"""Stage B rehearsal preflight for optional DAW session tooling."""
import logging

from modulation_arrangement import (
    DAWUnavailableError,
    check_daw_availability,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stage_b_rehearsal_preflight")

try:
    report = check_daw_availability(require_ardour=False, require_carla=False, log=logger)
except DAWUnavailableError as exc:  # pragma: no cover - shell invocation path
    logger.warning("%s", exc)
    logger.warning(
        "Stage B rehearsals will skip DAW session file export until the executables are installed."
    )
else:
    missing = [name for name, available in report.items() if not available]
    if missing:
        logger.warning(
            "Optional DAW tools missing for session export: %s", ", ".join(sorted(missing))
        )
    else:
        logger.info("Ardour and Carla executables detected; session exports enabled.")
PY
