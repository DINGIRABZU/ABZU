# Vector Memory

The `vector_memory` module provides a lightweight FAISS/SQLite backed store for
text embeddings. Entries are logged, decayed over time and can be searched or
clustered to discover emerging themes.

## Snapshot persistence

Every write increments an operation counter. When the counter reaches the
configured `snapshot_interval`, the store writes a snapshot to
`settings.vector_db_path/snapshots`. Snapshots can also be managed manually:

```python
from vector_memory import persist_snapshot, restore_latest_snapshot

path = persist_snapshot()           # write a timestamped snapshot
restore_latest_snapshot()           # restore most recent snapshot
```

These helpers simplify rollbacks in higher level pipelines such as auto
retraining.

## Clustering

`cluster_vectors(k)` groups stored embeddings into `k` clusters using FAISS when
available, falling back to scikit-learn's `KMeans`. Each cluster summary contains
the cluster index and number of members.
