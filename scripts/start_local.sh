#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR/.."
cd "$ROOT_DIR"

# Launch containers, building images if needed
docker-compose up --build -d

# Wait for the service to be ready on port 8000
echo "Waiting for localhost:8000 to become available..."
until nc -z localhost 8000; do
  sleep 1
done

# Open the web console in the default browser
python -m webbrowser "web_console/index.html"
