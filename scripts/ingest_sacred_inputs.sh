#!/usr/bin/env bash
# Parse and embed sacred input files into the vector database
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

TMP_FILE="$(mktemp)"

python "$ROOT_DIR/rag_parser.py" --dir "$ROOT_DIR/sacred_inputs" > "$TMP_FILE"
python "$ROOT_DIR/spiral_embedder.py" --in "$TMP_FILE"

rm -f "$TMP_FILE"
