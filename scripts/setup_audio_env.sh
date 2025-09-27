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

PYTHON_BIN="python3"
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

echo "Installing Stage B audio extras..."

install_python_package() {
  local package="$1"
  local dist=""
  local expected=""
  if [[ "$package" == *"=="* ]]; then
    dist="${package%%==*}"
    expected="${package##*==}"
  fi

  if [[ -n "$dist" && -n "$expected" ]]; then
    if "$PYTHON_BIN" - "$dist" "$expected" <<'PY'; then
import sys
from importlib import metadata

dist, expected = sys.argv[1:3]
try:
    version = metadata.version(dist)
except metadata.PackageNotFoundError:
    sys.exit(1)
if version == expected:
    sys.exit(0)
sys.exit(1)
PY
      echo "${dist}==${expected} already satisfied"
      return 0
    fi
  fi

  if "$PYTHON_BIN" -m pip install "$package"; then
    return 0
  fi

  echo "Retrying $package installation without dependency resolution" >&2
  "$PYTHON_BIN" -m pip install --no-deps "$package"
}

for package in \
  "pydub==0.25.1" \
  "simpleaudio==1.0.4" \
  "soundfile==0.13.1" \
  "librosa==0.11.0" \
  "opensmile==2.6.0" \
  "EmotiVoice==0.2.0"; do
  install_python_package "$package"
done

for local_package in \
  "$ROOT_DIR/vendor/clap_stub" \
  "$ROOT_DIR/vendor/rave_stub"; do
  install_python_package "$local_package"
done

echo "Validating Python audio dependencies..."
"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import importlib
import shutil
import ctypes
from importlib import metadata
import sys
from ctypes.util import find_library

REQUIREMENTS = [
    ("pydub", "pydub", "0.25.1", True),
    ("simpleaudio", "simpleaudio", "1.0.4", True),
    ("soundfile", "soundfile", "0.13.1", True),
    ("librosa", "librosa", "0.11.0", True),
    ("opensmile", "opensmile", "2.6.0", True),
    ("EmotiVoice", "emotivoice", "0.2.0", False),
    ("clap", "clap", "0.7.1.post1", False),
    ("rave", "rave", "0.1.0", False),
]

errors: list[str] = []
warnings: list[str] = []

def _check_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise RuntimeError("ffmpeg binary not found in PATH")
    return path


def _load_library(name: str, fallbacks: tuple[str, ...]) -> str:
    candidates: list[str] = []
    resolved = find_library(name)
    if resolved:
        candidates.append(resolved)
    candidates.extend(fallbacks)
    last_error: Exception | None = None
    for candidate in candidates:
        try:
            ctypes.CDLL(candidate)
        except OSError as exc:
            last_error = exc
        else:
            return candidate
    message = str(last_error) if last_error else f"unable to locate shared library for {name}"
    raise RuntimeError(message)


SYSTEM_REQUIREMENTS = [
    ("ffmpeg", True, _check_ffmpeg),
    ("libsndfile", True, lambda: _load_library("sndfile", ("libsndfile.so.1",))),
    ("libasound", True, lambda: _load_library("asound", ("libasound.so.2",))),
]

system_status: list[str] = []

for dist_name, module_name, expected_version, required in REQUIREMENTS:
    try:
        installed_version = metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        target = errors if required else warnings
        target.append(f"{dist_name} distribution not installed")
    else:
        if installed_version != expected_version:
            target = errors if required else warnings
            target.append(
                f"{dist_name} version mismatch: {installed_version} (expected {expected_version})"
            )

    try:
        importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - invoked from shell script
        target = errors if required else warnings
        target.append(f"{module_name} import failed: {exc}")

for name, required, checker in SYSTEM_REQUIREMENTS:
    try:
        resolved = checker()
    except Exception as exc:  # pragma: no cover - shell invocation path
        target = errors if required else warnings
        target.append(f"{name} check failed: {exc}")
    else:
        if isinstance(resolved, str):
            system_status.append(f"{name}:{resolved}")
        else:
            system_status.append(f"{name}")

if errors:
    print("Audio dependency validation failed:", file=sys.stderr)
    for item in errors:
        print(f" - {item}", file=sys.stderr)
    sys.exit(1)

if warnings:
    print("Audio dependency warnings detected:", file=sys.stderr)
    for item in warnings:
        print(f" - {item}", file=sys.stderr)

print(
    "Audio dependencies verified: "
    + ", ".join(f"{name}=={version}" for name, _, version, _ in REQUIREMENTS)
)
if system_status:
    print("System dependencies verified: " + ", ".join(system_status))
PY

export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

echo "Validating audio stack..."
"$PYTHON_BIN" -m audio.check_env --strict

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
