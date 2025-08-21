#!/bin/bash
# Launch servant models defined in SERVANT_MODELS and record reachable endpoints
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Verify prerequisites
if ! bash scripts/check_prereqs.sh >/dev/null 2>&1; then
    echo "Prerequisite check failed. Run scripts/check_prereqs.sh for details." >&2
    exit 1
fi

for cmd in curl docker python; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Required command not found: $cmd" >&2
        exit 1
    fi
done

LOG_FILE="${SERVANT_LOG_FILE:-$ROOT/servant_launch.log}"
: >"$LOG_FILE"
log() { echo "$@" | tee -a "$LOG_FILE"; }

if [ -f "secrets.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "secrets.env"
    set +a
else
    echo "secrets.env not found" >&2
    exit 1
fi

SERVANTS_FILE="${SERVANT_ENDPOINTS_FILE:-$ROOT/servant_endpoints.tmp}"
: >"$SERVANTS_FILE"

if [ -z "${SERVANT_MODELS:-}" ]; then
    cat <<'EOF' >&2
Warning: SERVANT_MODELS is not set; no servant models will be launched.
Define SERVANT_MODELS in secrets.env or export it before running.
Example:
  export SERVANT_MODELS="deepseek=http://localhost:8002,mistral=http://localhost:8003"
EOF
    exit 0
fi

wait_health() {
    local name="$1"
    local url="$2"
    local health="${url%/}/health"
    local timeout="${SERVANT_TIMEOUT:-60}"
    for ((i=0; i<timeout; i++)); do
        if curl -fsS "$health" >/dev/null 2>&1; then
            log "Health check passed for $name at $health"
            return 0
        fi
        sleep 1
    done
    log "Health check failed for $name at $health"
    return 1
}

launch_model() {
    local name="$1"
    local url="$2"
    local model_dir="$3"
    local image="$4"

    log "Launching servant $name at $url"
    if [ -z "$url" ]; then
        log "No URL provided for $name; skipping"
        return
    fi

    if [[ "$url" == http://localhost:* || "$url" == http://127.0.0.1:* ]]; then
        local port="${url##*:}"
        port="${port%%/*}"
        if [ -n "$model_dir" ] && [ ! -d "$model_dir" ]; then
            case "$name" in
                deepseek)
                    python download_models.py deepseek_v3 ;;
                mistral)
                    python download_models.py mistral_8x22b --int8 ;;
                kimi_k2)
                    python download_models.py kimi_k2 ;;
            esac
        fi
        if [ -n "$model_dir" ]; then
            if command -v docker >/dev/null 2>&1; then
                docker pull "$image" >/dev/null 2>&1 || true
                local cmd="docker run -d --rm -v \"$model_dir\":/model -p \"$port\":8000 --name \"${name}_service\" \"$image\""
                log "$cmd"
                eval "$cmd"
            else
                local cmd="python -m vllm.entrypoints.openai.api_server --model \"$model_dir\" --port \"$port\""
                log "$cmd"
                eval "$cmd &"
            fi
        fi
    else
        log "Using remote servant at $url; no launch command executed"
    fi

    wait_health "$name" "$url"
    echo "${name}=${url}" >>"$SERVANTS_FILE"
}

IFS=','
for item in $SERVANT_MODELS; do
    name="${item%%=*}"
    url="${item#*=}"
    case "$name" in
        deepseek)
            launch_model "$name" "$url" "INANNA_AI/models/DeepSeek-V3" "deepseek-service:latest" ;;
        mistral)
            launch_model "$name" "$url" "INANNA_AI/models/Mistral-8x22B" "mistral-service:latest" ;;
        kimi_k2)
            launch_model "$name" "$url" "INANNA_AI/models/Kimi-K2" "kimi-k2-service:latest" ;;
        *)
            launch_model "$name" "$url" "" "" ;;
    esac
done
