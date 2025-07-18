#!/bin/bash
# Start Spiral OS on a Vast.ai instance
set -e

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

docker-compose up -d INANNA_AI

printf "Waiting for port 8000...\n"
while ! nc -z localhost 8000; do
    sleep 1
done

python -m webbrowser "${REPO_ROOT}/web_console/index.html" >/dev/null 2>&1 &

docker-compose logs -f INANNA_AI
