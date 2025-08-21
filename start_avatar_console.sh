#!/bin/bash
# Launch Crown console alongside the avatar stream and tail the logs.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

CROWN_PID=""
STREAM_PID=""
TAIL_PID=""

cleanup() {
    [[ -n "$CROWN_PID" ]] && kill "$CROWN_PID" >/dev/null 2>&1 || true
    [[ -n "$STREAM_PID" ]] && kill "$STREAM_PID" >/dev/null 2>&1 || true
    [[ -n "$TAIL_PID" ]] && kill "$TAIL_PID" >/dev/null 2>&1 || true
}

trap 'cleanup; exit 1' INT TERM

# Start Crown services in the background
./start_crown_console.sh &
CROWN_PID=$!

# Optional scaling for the avatar stream
ARGS=()
if [ -n "${AVATAR_SCALE:-}" ]; then
    ARGS+=(--scale "$AVATAR_SCALE")
fi

python video_stream.py "${ARGS[@]}" &
STREAM_PID=$!

LOG_FILE="logs/INANNA_AI.log"
while [ ! -f "$LOG_FILE" ]; do
    sleep 1
done

tail -f "$LOG_FILE" &
TAIL_PID=$!

set +e
wait "$CROWN_PID"
CROWN_STATUS=$?
wait "$STREAM_PID"
STREAM_STATUS=$?
set -e

kill "$TAIL_PID" >/dev/null 2>&1 || true
wait "$TAIL_PID" 2>/dev/null || true

if (( CROWN_STATUS != 0 )); then
    echo "Crown process exited with status $CROWN_STATUS" >&2
fi
if (( STREAM_STATUS != 0 )); then
    echo "Stream process exited with status $STREAM_STATUS" >&2
fi
if (( CROWN_STATUS != 0 || STREAM_STATUS != 0 )); then
    exit 1
fi
