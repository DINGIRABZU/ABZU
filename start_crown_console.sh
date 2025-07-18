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

if [ -f "launch_servants.sh" ]; then
    ./launch_servants.sh
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

for url in "${DEEPSEEK_URL:-}" "${MISTRAL_URL:-}" "${KIMI_K2_URL:-}"; do
    if [[ "$url" == http://localhost:* || "$url" == http://127.0.0.1:* ]]; then
        wait_port "$(parse_port "$url")"
    fi
done

python console_interface.py
