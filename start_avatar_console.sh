#!/bin/bash
# Launch Crown console alongside the avatar stream and tail the logs.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

CROWN_PID=""
STREAM_PID=""
TAIL_PID=""
CROWN_STATUS=""
STREAM_STATUS=""

cleanup() {
    trap - EXIT INT TERM
    [[ -n "$TAIL_PID" ]] && kill "$TAIL_PID" >/dev/null 2>&1 || true
    [[ -n "$CROWN_PID" ]] && kill "$CROWN_PID" >/dev/null 2>&1 || true
    [[ -n "$STREAM_PID" ]] && kill "$STREAM_PID" >/dev/null 2>&1 || true
    if [[ -z "$CROWN_STATUS" && -n "$CROWN_PID" ]]; then
        wait "$CROWN_PID" 2>/dev/null; CROWN_STATUS=$?
    fi
    if [[ -z "$STREAM_STATUS" && -n "$STREAM_PID" ]]; then
        wait "$STREAM_PID" 2>/dev/null; STREAM_STATUS=$?
    fi
    if [[ -n "$TAIL_PID" ]]; then
        wait "$TAIL_PID" 2>/dev/null || true
    fi
    if (( CROWN_STATUS != 0 )); then
        echo "Crown process exited with status $CROWN_STATUS" >&2
    fi
    if (( STREAM_STATUS != 0 )); then
        echo "Stream process exited with status $STREAM_STATUS" >&2
    fi
    if (( CROWN_STATUS != 0 || STREAM_STATUS != 0 )); then
        exit 1
    fi
}

trap cleanup EXIT INT TERM

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
LOG_TIMEOUT=${LOG_TIMEOUT:-30}
elapsed=0
while [[ ! -f "$LOG_FILE" && $elapsed -lt $LOG_TIMEOUT ]]; do
    sleep 1
    elapsed=$((elapsed + 1))
done
if [[ ! -f "$LOG_FILE" ]]; then
    echo "Log file $LOG_FILE not found after $LOG_TIMEOUT seconds" >&2
    exit 1
fi

tail -f "$LOG_FILE" &
TAIL_PID=$!

set +e
wait "$CROWN_PID"; CROWN_STATUS=$?
wait "$STREAM_PID"; STREAM_STATUS=$?
set -e

if (( CROWN_STATUS != 0 || STREAM_STATUS != 0 )); then
    exit 1
fi
