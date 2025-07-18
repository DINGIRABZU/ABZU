#!/usr/bin/env bash
# Install all development dependencies listed in dev-requirements.txt
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

pip install -r "$ROOT_DIR/dev-requirements.txt"
