# Memory Architecture

The cortex memory stores a chronological log of spiral decisions in a JSONL
file located at `data/cortex_memory_spiral.jsonl`. Each entry captures the
serialized state of the node, the decision payload, and a UTC timestamp.

## Indexing

Entries may provide a list of semantic `tags` in the decision payload. These
are tracked in an inverted index (`data/cortex_memory_index.json`) mapping each
tag to the identifiers of entries containing it. The index accelerates
retrieval for tag-based queries and is updated atomically when new spirals are
recorded.

## Concurrency

Read and write access to the memory and index files is synchronized with a
lightweight reader/writer lock. Recording a spiral acquires the write lock
while queries take the read lock, allowing concurrent reads but exclusive
writes.

## Schema Evolution

Entries are stored as standalone JSON objects.  New fields can therefore be
introduced to the decision payload over time without requiring a migration of
existing records.  Older entries simply omit the additional keys and continue
to be readable.  Rebuilding the index via maintenance utilities such as
`prune_spirals` recreates the inverted and full‑text structures in the latest
format, keeping the log forwards compatible.

## Utilities

The `memory.cortex` module exposes helpers to manage the log:

- `prune_spirals(keep)` – retain only the most recent `keep` entries.
- `export_spirals(path, tags=None, filter=None)` – export matching entries to a
  JSON file.
- `query_spirals(filter=None, tags=None)` – retrieve entries filtered by
  decision fields or semantic tags.

A small CLI wrapper `memory.cortex_cli` provides access to these functions.
