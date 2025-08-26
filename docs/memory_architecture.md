# Memory Architecture

This project blends several complementary memory systems to capture context and
long‑term knowledge.

## Cortex memory

`memory/cortex.py` persists application state as JSON lines while maintaining an
inverted index for semantic tags and a full‑text index for tag tokens. Reader
and writer locks guard the log and index so multiple threads can record and
query safely. Helper utilities allow concurrent queries and pruning of old
entries.

## Vector memory store

`memory_store.py` combines SQLite persistence with an in‑memory similarity index
using FAISS. When optional dependencies such as `faiss` or `numpy` are missing
it transparently falls back to a pure Python implementation. The database schema
is automatically migrated to include new columns, preserving compatibility with
older snapshots.

## Other memories

Specialised modules like `vector_memory.py` and `spiral_memory.py` provide
additional stores for short text snippets and ritual state. Together these
components form a layered architecture where symbolic records, vectors and
higher order reasoning coexist.
