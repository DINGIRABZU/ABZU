#!/bin/bash
# Minimal startup for INANNA core
set -euo pipefail

MEM_DIR=${MEMORY_DIR:-data/vector_memory}
# Create required memory directories
mkdir -p "$MEM_DIR"/{vector_memory,chroma}

# Launch servant model endpoints
export SERVANT_MODELS=${SERVANT_MODELS:-"deepseek=http://localhost:8002,mistral=http://localhost:8003"}
"$(dirname "$0")"/../launch_servants.sh

# Initialize INANNA core to verify configuration
python - <<'PY'
from init_crown_agent import initialize_crown
initialize_crown()
print("INANNA core initialized")
PY
