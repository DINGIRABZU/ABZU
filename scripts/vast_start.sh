#!/bin/bash
# Start Spiral OS on a Vast.ai instance
set -e

if ! command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose is required" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/.."

# Source environment variables if secrets.env exists
if [ -f "$REPO_ROOT/secrets.env" ]; then
    set -a
    source "$REPO_ROOT/secrets.env"
    set +a
fi

if [ "$1" = "--setup" ]; then
    bash "$SCRIPT_DIR/setup_vast_ai.sh"
    bash "$SCRIPT_DIR/setup_glm.sh"
fi

cd "$REPO_ROOT"

if ! docker-compose up -d INANNA_AI; then
    echo "docker-compose failed" >&2
    exit 1
fi

printf "Waiting for port 8000...\n"
PORT_READY=0
for i in {1..60}; do
    if nc -z localhost 8000; then
        PORT_READY=1
        break
    fi
    sleep 1
done

if [ "$PORT_READY" -ne 1 ]; then
    echo "Port 8000 did not become available" >&2
    exit 1
fi

python -m webbrowser "${REPO_ROOT}/web_console/index.html" >/dev/null 2>&1 &

docker-compose logs -f INANNA_AI
