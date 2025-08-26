# Recovery Playbook

This guide outlines steps to restore vector memory state from snapshots.

1. **Locate snapshots**
   - Snapshot files are listed in `snapshots/manifest.json` under the vector memory directory.
   - Each entry records the absolute path of a persisted snapshot.
2. **Select a snapshot**
   - Choose the desired path from the manifest. The last entry is typically the most recent.
3. **Restore**
   - Use `vector_memory.restore(<path>)` to load a specific snapshot, or
     call `vector_memory.restore_latest_snapshot()` to automatically load
     the newest entry.
4. **Verify**
   - After restoration, run existing workflows or tests to ensure the
     vector store has returned to the expected state.

This procedure provides a repeatable method for recovery using the
snapshot manifest.
