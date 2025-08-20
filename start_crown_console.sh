#!/bin/bash
# Launch Crown services, wait for local endpoints, and start the console.
# Uses 'nc' when available or falls back to a Python socket check.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

./scripts/check_prereqs.sh

if [ -f "secrets.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "secrets.env"
    set +a
else
    echo "secrets.env not found" >&2
    exit 1
fi

./crown_model_launcher.sh

SERVANT_ENDPOINTS_FILE="$(mktemp)"
export SERVANT_ENDPOINTS_FILE
if [ -f "launch_servants.sh" ]; then
    ./launch_servants.sh
    if [ -f "$SERVANT_ENDPOINTS_FILE" ]; then
        SERVANT_MODELS="$(paste -sd, "$SERVANT_ENDPOINTS_FILE")"
        export SERVANT_MODELS
        rm -f "$SERVANT_ENDPOINTS_FILE"
    fi
fi

if command -v nc >/dev/null 2>&1; then
    HAS_NC=1
else
    HAS_NC=0
fi

wait_port() {
    local port=$1
    printf 'Waiting for port %s...\n' "$port"
    if [ "$HAS_NC" -eq 1 ]; then
        while ! nc -z localhost "$port"; do
            sleep 1
        done
    else
        python - "$port" <<'EOF'
import socket
import sys
import time

port = int(sys.argv[1])
while True:
    try:
        with socket.create_connection(("localhost", port), timeout=1):
            break
    except OSError:
        time.sleep(1)
EOF
    fi
}

parse_port() {
    local url=$1
    local port="${url##*:}"
    echo "${port%%/*}"
}

main_port=$(parse_port "$GLM_API_URL")
wait_port "$main_port"

IFS=','
for item in ${SERVANT_MODELS:-}; do
    url="${item#*=}"
    if [[ "$url" == http://localhost:* || "$url" == http://127.0.0.1:* ]]; then
        wait_port "$(parse_port "$url")"
    fi
done
unset IFS

python -m cli.console_interface
