#!/usr/bin/env bash
# Verify required secrets and external commands are available, and load secrets if present
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Source secrets.env if it exists, exporting variables
if [ -f "$ROOT_DIR/secrets.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$ROOT_DIR/secrets.env"
    set +a
fi

# Ensure required secrets are set, fail fast if any are missing
for var in HF_TOKEN GLM_API_URL GLM_API_KEY; do
    if [ -z "${!var:-}" ]; then
        echo "Missing required environment variable $var." >&2
        echo "Populate secrets.env with a value for $var and retry." >&2
        exit 1
    fi
done

missing=0

for cmd in docker nc sox ffmpeg curl jq wget aria2c; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Requirement missing: $cmd is not installed or not in PATH." >&2
        missing=1
    fi
done

if [ "$missing" -ne 0 ]; then
    exit 1
fi

echo "All requirements satisfied."
