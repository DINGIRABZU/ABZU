#!/bin/bash
# Build and run the OS Guardian container
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load environment variables if secrets.env exists
if [ -f "$REPO_ROOT/secrets.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$REPO_ROOT/secrets.env"
    set +a
fi

cd "$REPO_ROOT"

docker build -f docker/os_guardian.Dockerfile -t os_guardian .

docker run -it --rm \
    -e DISPLAY="${DISPLAY:-:0}" \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v "$REPO_ROOT":/workspace \
    -p 8000:8000 \
    os_guardian "$@"
