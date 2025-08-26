# Recovery Playbook

This guide outlines how to restore **vector memory** from persisted snapshots
and bring the narrative log back into alignment.

## Restoring a Snapshot

1. Review `snapshots/manifest.json` to locate available snapshot paths.
2. Load a specific snapshot:

   ```python
   from vector_memory import restore
   restore("path/to/snapshot.sqlite")
   ```

   To load the most recent snapshot automatically:

   ```python
   from vector_memory import restore_latest_snapshot
   restore_latest_snapshot()
   ```

## Narrative Resynchronization

Every call to `vector_memory.snapshot()` records a narrative `sacrifice`
entry in `data/narrative.log`. After restoring a snapshot:

1. Inspect the log for the last sacrifice entry to confirm the restored path.
2. Append new narrative events as activity resumes so the story timeline
   stays continuous.

This process ensures both data and narrative context are brought back
together after a system recovery.
