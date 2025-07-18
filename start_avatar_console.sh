#!/bin/bash
# Launch Crown console alongside the avatar stream and tail the logs.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

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

wait "$CROWN_PID" "$STREAM_PID"
kill "$TAIL_PID"
