# Memory Layer

The `memory.cortex` module stores spiral decisions and maintains an index for
fast retrieval. Each entry is appended to `data/cortex_memory_spiral.jsonl` and
metadata is written to `data/cortex_memory_index.json`.

## Hash-based tag lookups

Tags are recorded in plain text and by a deterministic SHA256 hash. Use
`hash_tag` to compute the hash and query the index without revealing the
original tag:

```python
from memory import cortex

h = cortex.hash_tag("quick")
ids = cortex.search_index(tag_hashes=[h])
entries = cortex.query_spirals(tag_hashes=[h])
```

## Concurrency

Reads and writes are protected by a reader/writer lock combined with a file
lock. Multiple threads or processes can safely interact with the memory files
without corrupting the index.

```python
from concurrent.futures import ThreadPoolExecutor
from memory import cortex

node = ...  # object implementing the SpiralNode protocol

def writer(i):
    cortex.record_spiral(node, {"num": i, "tags": [f"t{i}"]})

with ThreadPoolExecutor(max_workers=4) as ex:
    for i in range(10):
        ex.submit(writer, i)
```

## Snapshot restoration

Vector embeddings can be backed up and recovered using helper functions from
`vector_memory`. Writing a snapshot saves the current collection under the
configured database directory:

```python
from vector_memory import persist_snapshot, restore_latest_snapshot

snap = persist_snapshot()  # writes to <db_path>/snapshots
```

If the main database files are lost, the most recent snapshot can be restored
before continuing operations:

```python
restored = restore_latest_snapshot()
assert restored, "no snapshot found"
```

The `snapshots/manifest.json` file tracks available snapshots and is updated
whenever a new one is persisted.

