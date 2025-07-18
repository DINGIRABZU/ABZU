#!/bin/bash
# Simple wrapper for spiral_cortex_terminal.py
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

python spiral_cortex_terminal.py "$@"
