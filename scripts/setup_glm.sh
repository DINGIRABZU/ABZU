#!/bin/bash
# Setup GLM environment and directories
set -e

# install Python dependencies
pip install -r requirements.txt

# create directories for data and logs
mkdir -p /INANNA_AI
mkdir -p /QNL_LANGUAGE
mkdir -p /audit_logs

# copy the ethics policy to key directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cp "$ROOT_DIR/docs/ETHICS_POLICY.md" /INANNA_AI/ETHICS_POLICY.md
cp "$ROOT_DIR/docs/ETHICS_POLICY.md" /QNL_LANGUAGE/ETHICS_POLICY.md

cat <<'EON' > /audit_logs/README.txt
Audit logs for monitoring system behavior.
See /INANNA_AI/ETHICS_POLICY.md for the data policy.
EON

printf "Setup complete.\n"
