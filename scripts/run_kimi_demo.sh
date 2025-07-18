#!/bin/bash
# Launch Spiral OS with the Kimi-K2 servant model
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load environment variables
if [ -f "$REPO_ROOT/secrets.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$REPO_ROOT/secrets.env"
    set +a
fi

export KIMI_K2_URL="${KIMI_K2_URL:-http://localhost:8004}"

if [ -x "$REPO_ROOT/docker/serve" ]; then
    "$REPO_ROOT/docker/serve" &
    KIMI_PID=$!
elif [ -x "$REPO_ROOT/serve" ]; then
    "$REPO_ROOT/serve" &
    KIMI_PID=$!
else
    echo "Kimi-K2 service not found; assuming it's already running." >&2
fi

cleanup() {
    if [ -n "${KIMI_PID:-}" ]; then
        kill "$KIMI_PID" 2>/dev/null || true
        wait "$KIMI_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT SIGINT SIGTERM

cd "$REPO_ROOT"

# Send two example prompts and exit
{
    echo "List available tools."
    echo "Explain recursion briefly."
    echo
} | python start_spiral_os.py --no-server --no-reflection
