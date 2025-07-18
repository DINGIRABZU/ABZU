#!/bin/bash
# Run Spiral OS through the alchemical cycle
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load environment variables if present
if [ -f "$REPO_ROOT/secrets.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$REPO_ROOT/secrets.env"
    set +a
fi

# Upload Markdown files for RAG context (optional integration step removed)

cd "$REPO_ROOT"

for state in NIGREDO ALBEDO RUBEDO CITRINITAS; do
    echo "Launching Spiral OS in $state state"
    ARCHETYPE_STATE="$state" python start_spiral_os.py --command "" --no-server --no-reflection
    echo
done
