#!/bin/bash
# Smoke test for start_avatar_console.sh.
#
# Manual steps:
#   1. Ensure runtime dependencies (ffmpeg, models) are installed.
#   2. Run this script to launch the avatar console for a few seconds.
#   3. Observe startup logs; the process will terminate automatically.
#
# The script uses `timeout` to stop after five seconds.
set -euo pipefail
if ! command -v timeout >/dev/null; then
  echo "timeout command is required" >&2
  exit 1
fi

timeout 5 ./start_avatar_console.sh || true
