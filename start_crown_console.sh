#!/bin/bash
# Launch Crown services, verify health endpoints, and start the console.
# Each service is polled via its /health endpoint before the REPL begins.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Display welcome banner
if ! python scripts/welcome_banner.py; then
    echo "welcome banner failed" >&2
    exit 1
fi

# Ensure external requirements are present
if ! ./scripts/check_requirements.sh >/dev/null 2>&1; then
    echo "Requirement check failed. Run scripts/check_requirements.sh for details." >&2
    exit 1
fi

if [ -f "secrets.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "secrets.env"
    set +a
else
    echo "secrets.env not found" >&2
    exit 1
fi

if ! ./crown_model_launcher.sh; then
    echo "crown_model_launcher.sh failed" >&2
    exit 1
fi

SERVANT_ENDPOINTS_FILE="$(mktemp)"
trap 'rm -f "$SERVANT_ENDPOINTS_FILE"' EXIT INT TERM ERR
export SERVANT_ENDPOINTS_FILE
if [ -f "launch_servants.sh" ]; then
    if ! ./launch_servants.sh; then
        echo "launch_servants.sh failed" >&2
        exit 1
    fi
    if [ -f "$SERVANT_ENDPOINTS_FILE" ]; then
        SERVANT_MODELS="$(paste -sd, "$SERVANT_ENDPOINTS_FILE")"
        export SERVANT_MODELS
    fi
fi

wait_health() {
    local name="$1"
    local url="$2"
    local health="${url%/}/health"
    local timeout="${HEALTH_TIMEOUT:-60}"
    local status msg
    printf 'Waiting for %s health at %s...\n' "$name" "$health"
    for ((i=0; i<timeout; i++)); do
        status=$(curl -o /dev/null -s -w "%{http_code}" "$health" || echo "000")
        if [[ "$status" =~ ^2 ]]; then
            return 0
        fi
        case "$status" in
            401) msg="401 Unauthorized – check GLM_API_KEY" ;;
            403) msg="403 Forbidden – verify permissions" ;;
            404) msg="404 Not Found" ;;
            000) msg="Connection failed" ;;
            *)   msg="HTTP $status" ;;
        esac
        echo "$name health check attempt $((i+1))/$timeout: $msg" >&2
        sleep 1
    done
    echo "$name failed health check at $health" >&2
    return 1
}

if ! wait_health "GLM" "$GLM_API_URL"; then
    exit 1
fi

IFS=','
for item in ${SERVANT_MODELS:-}; do
    name="${item%%=*}"
    url="${item#*=}"
    if ! wait_health "$name" "$url"; then
        exit 1
    fi
done
unset IFS

python -m cli.console_interface
