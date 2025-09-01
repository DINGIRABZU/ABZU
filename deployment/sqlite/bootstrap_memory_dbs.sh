#!/usr/bin/env bash
# Bootstrap SQLite databases used by memory layers.
# Usage: ./bootstrap_memory_dbs.sh [data_dir]
set -euo pipefail
DATA_DIR=${1:-data}
mkdir -p "$DATA_DIR"
sqlite3 "$DATA_DIR/emotions.db" "VACUUM;"
sqlite3 "$DATA_DIR/ontology.db" "VACUUM;"
sqlite3 "$DATA_DIR/narrative_engine.db" "VACUUM;"
echo "Initialized emotions.db, ontology.db and narrative_engine.db under $DATA_DIR"
