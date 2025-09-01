#!/usr/bin/env bash
# Initialize memory stores with sample data and show retrieval
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$ROOT_DIR/data"
mkdir -p "$DATA_DIR"

# Configure file-based back-ends
export CORTEX_BACKEND=file
export CORTEX_PATH="$DATA_DIR/cortex.jsonl"
export EMOTION_BACKEND=file
export EMOTION_DB_PATH="$DATA_DIR/emotions.db"
export MENTAL_BACKEND=file
export MENTAL_JSON_PATH="$DATA_DIR/tasks.jsonl"
export SPIRIT_BACKEND=file
export SPIRITUAL_DB_PATH="$DATA_DIR/ontology.db"
export NARRATIVE_BACKEND=file
export NARRATIVE_LOG_PATH="$DATA_DIR/story.log"

python - <<'PY'
from memory.cortex import record_spiral, query_spirals
from memory.emotional import log_emotion, fetch_emotion_history, get_connection as emotion_conn
try:
    from memory.mental import record_task_flow, query_related_tasks
except Exception:  # mental layer optional
    record_task_flow = query_related_tasks = None
from memory.spiritual import map_to_symbol, lookup_symbol_history, get_connection as spirit_conn
from memory.narrative_engine import log_story, stream_stories

class Node:
    children = []

record_spiral(Node(), {"result": "demo", "tags": ["example"]})
log_emotion([0.8], conn=emotion_conn())
if record_task_flow and query_related_tasks:
    record_task_flow("taskA", {"step": 1})
conn_spirit = spirit_conn()
map_to_symbol(("eclipse", "\u263E"), conn=conn_spirit)
log_story("hero meets guide")

print("Cortex:", query_spirals(tags=["example"]))
print("Emotional:", fetch_emotion_history(60, conn=emotion_conn()))
if record_task_flow and query_related_tasks:
    print("Mental:", query_related_tasks("taskA"))
else:
    print("Mental: skipped (missing dependencies)")
print("Spiritual:", lookup_symbol_history("\u263E", conn=conn_spirit))
print("Narrative:", list(stream_stories()))
PY
