#!/usr/bin/env bash
set -euo pipefail

# Regenerate documentation artifacts and verify no stale files remain.
ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT"

python tools/doc_indexer.py
python scripts/component_inventory.py
python scripts/validate_api_schemas.py
# Validate links across markdown files
git ls-files '*.md' | xargs python scripts/validate_links.py

# Ensure indexes are committed
git diff --exit-code docs/INDEX.md docs/component_index.md docs/component_status.md docs/component_status.json docs/schemas/openapi.json || {
  echo "Documentation artifacts are out of date. Run build_docs.sh and commit the results." >&2
  exit 1
}
