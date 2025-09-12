#!/bin/bash
# Patent pending – see PATENTS.md
# Launch GLM model with environment setup
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Load secrets
if [ -f "secrets.env" ]; then
    set -a
    source "secrets.env"
    set +a
else
    echo "secrets.env not found. Create it by copying secrets.env.template: cp secrets.env.template secrets.env, then edit it with your API keys and URLs." >&2
    exit 1
fi

: "${HF_TOKEN?HF_TOKEN not set}"
: "${GLM_API_URL?GLM_API_URL not set}"
: "${GLM_API_KEY?GLM_API_KEY not set}"

# Ensure required tools are available
for cmd in jq curl; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "$cmd is required but not installed. Please install $cmd." >&2
        exit 1
    fi
done

parse_port() {
    local url=$1
    if [[ $url =~ :([0-9]+) ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        echo "8000"
    fi
}

MODEL_PORT=$(parse_port "$GLM_API_URL")

MODEL_DIR="INANNA_AI/models/GLM-4.1V-9B"
mkdir -p "$MODEL_DIR"

# Locate an existing weight file, if any
WEIGHT_FILE=$(find "$MODEL_DIR" -type f \( -name '*.bin' -o -name '*.safetensors' \) | head -n 1)

if [ -z "$WEIGHT_FILE" ]; then
    echo "GLM weights not found. Fetching metadata…" >&2
    if ! META=$(curl -fsSL -H "Authorization: Bearer $HF_TOKEN" \
        https://huggingface.co/api/models/THUDM/glm-4.1v-9b); then
        echo "Failed to fetch model metadata" >&2
        exit 1
    fi
    FILE=$(echo "$META" | jq -r '.siblings[] | select(.rfilename|test("safetensors$|bin$")) | .rfilename' | head -n1)
    SHA256=$(echo "$META" | jq -r ".siblings[] | select(.rfilename==\"$FILE\") | .lfs.sha256")
    SIZE=$(echo "$META" | jq -r ".siblings[] | select(.rfilename==\"$FILE\") | .lfs.size")
    URL="https://huggingface.co/THUDM/glm-4.1v-9b/resolve/main/$FILE"
    echo "Downloading $FILE…" >&2
    if command -v aria2c >/dev/null 2>&1; then
        aria2c --header "Authorization: Bearer $HF_TOKEN" -d "$MODEL_DIR" -o "$FILE" "$URL"
    else
        wget --header "Authorization: Bearer $HF_TOKEN" -O "$MODEL_DIR/$FILE" "$URL"
    fi
    WEIGHT_FILE="$MODEL_DIR/$FILE"
else
    FILE="$(basename "$WEIGHT_FILE")"
    if ! META=$(curl -fsSL -H "Authorization: Bearer $HF_TOKEN" \
        https://huggingface.co/api/models/THUDM/glm-4.1v-9b); then
        echo "Failed to fetch model metadata" >&2
        exit 1
    fi
    SHA256=$(echo "$META" | jq -r ".siblings[] | select(.rfilename==\"$FILE\") | .lfs.sha256")
    SIZE=$(echo "$META" | jq -r ".siblings[] | select(.rfilename==\"$FILE\") | .lfs.size")
fi

# Validate checksum and size
calc_sha=$(sha256sum "$WEIGHT_FILE" | awk '{print $1}')
if [ "$calc_sha" != "$SHA256" ]; then
    echo "Checksum mismatch for $WEIGHT_FILE" >&2
    exit 1
fi
calc_size=$(stat -c%s "$WEIGHT_FILE")
if [ "$calc_size" != "$SIZE" ]; then
    echo "Size mismatch for $WEIGHT_FILE" >&2
    exit 1
fi

# Start the model server
if command -v docker >/dev/null 2>&1; then
    docker run -d --rm -v "$MODEL_DIR":/model -p "${MODEL_PORT}:8000" \
        -e GLM_API_URL="$GLM_API_URL" -e GLM_API_KEY="$GLM_API_KEY" \
        --name glm_service glm-service:latest
else
    python -m vllm.entrypoints.openai.api_server --model "$MODEL_DIR" --port "$MODEL_PORT" &
fi

# Wait for health endpoint
for i in {1..30}; do
    if curl -sf "http://localhost:${MODEL_PORT}/health" >/dev/null; then
        break
    fi
    sleep 1
done

curl -sf "http://localhost:${MODEL_PORT}/health" >/dev/null || {
    echo "Model server failed health check" >&2
    exit 1
}

printf '%s\n' "$MODEL_DIR"
