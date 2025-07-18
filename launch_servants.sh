#!/bin/bash
# Launch servant LLMs when configured with localhost URLs
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ -f "secrets.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "secrets.env"
    set +a
else
    echo "secrets.env not found" >&2
    exit 1
fi

launch_model() {
    local name="$1"
    local url="$2"
    local model_dir="$3"
    local image="$4"

    if [ -z "$url" ]; then
        return
    fi

    if [[ "$url" == http://localhost:* || "$url" == http://127.0.0.1:* ]]; then
        local port="${url##*:}"
        port="${port%%/*}"
        if [ ! -d "$model_dir" ]; then
            case "$name" in
                deepseek)
                    python download_models.py deepseek_v3 ;;
                mistral)
                    python download_models.py mistral_8x22b --int8 ;;
                kimi_k2)
                    python download_models.py kimi_k2 ;;
            esac
        fi
        if command -v docker >/dev/null 2>&1; then
            docker run -d --rm -v "$model_dir":/model -p "$port":8000 \
                --name "${name}_service" "$image"
        else
            python -m vllm.entrypoints.openai.api_server \
                --model "$model_dir" --port "$port" &
        fi
    fi
}

launch_model deepseek "${DEEPSEEK_URL:-}" "INANNA_AI/models/DeepSeek-V3" "deepseek-service:latest"
launch_model mistral "${MISTRAL_URL:-}" "INANNA_AI/models/Mistral-8x22B" "mistral-service:latest"
launch_model kimi_k2 "${KIMI_K2_URL:-}" "INANNA_AI/models/Kimi-K2" "kimi-k2-service:latest"
