#!/usr/bin/env bash
# Install pinned audio dependencies for Stage B rehearsals
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

install_ffmpeg() {
  if command -v ffmpeg >/dev/null 2>&1; then
    echo "ffmpeg binary already available"
    return 0
  fi

  echo "Installing ffmpeg binary..."

  if command -v apt-get >/dev/null 2>&1; then
    local sudo_cmd=""
    if command -v sudo >/dev/null 2>&1; then
      sudo_cmd="sudo "
    fi
    if ${sudo_cmd}apt-get update && ${sudo_cmd}apt-get install -y ffmpeg; then
      return 0
    fi
  elif command -v yum >/dev/null 2>&1; then
    local sudo_cmd=""
    if command -v sudo >/dev/null 2>&1; then
      sudo_cmd="sudo "
    fi
    if ${sudo_cmd}yum install -y ffmpeg; then
      return 0
    fi
  elif command -v brew >/dev/null 2>&1; then
    if brew install ffmpeg; then
      return 0
    fi
  fi

  echo "WARNING: automatic ffmpeg installation failed. Install it via your package manager." >&2
  return 1
}

install_ffmpeg || true

echo "Installing Stage B audio extras..."
pip install \
  pydub==0.25.1 \
  simpleaudio==1.0.4 \
  soundfile==0.13.1 \
  librosa==0.11.0 \
  opensmile==2.6.0 \
  EmotiVoice==0.2.0

pip install \
  "$ROOT_DIR/vendor/clap_stub" \
  "$ROOT_DIR/vendor/rave_stub"

echo "Validating audio stack..."
python -m audio.check_env --strict

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
