#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR/.."
cd "$ROOT_DIR"

"$SCRIPT_DIR/check_prereqs.sh"

if [ ! -f secrets.env ]; then
    cp secrets.env.template secrets.env
    echo "Configuring secrets.env"
    read -p "Enter HF_TOKEN: " HF_TOKEN
    read -p "Enter GLM_API_URL: " GLM_API_URL
    read -p "Enter GLM_API_KEY: " GLM_API_KEY
    sed -i "s|^HF_TOKEN=.*|HF_TOKEN=$HF_TOKEN|" secrets.env
    sed -i "s|^GLM_API_URL=.*|GLM_API_URL=$GLM_API_URL|" secrets.env
    sed -i "s|^GLM_API_KEY=.*|GLM_API_KEY=$GLM_API_KEY|" secrets.env
else
    echo "secrets.env already exists. Skipping secrets setup."
fi

read -p "Download DeepSeek-V3 model now? (Y/n): " download_choice
download_choice=${download_choice:-Y}
if [[ "$download_choice" =~ ^[Yy]$ ]]; then
    python download_models.py deepseek_v3
else
    echo "Skipping model download."
fi

echo "Easy setup complete."
