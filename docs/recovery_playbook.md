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

## Component Recovery

When a component fails during boot:

1. Review `razar/boot_orchestrator.log` for error details.
2. Run the component's health check manually to validate the fix:

   ```python
   from razar.health_checks import run
   run("basic_service")
   ```

3. Once the check passes, restart the boot sequence. If failures persist,
   quarantine the component and investigate configuration or environment
   issues before reattempting.

## Escalation Paths

- **First failure** – developer on duty addresses the issue and restores the
  service.
- **Repeated failures** – notify the operations channel and create an
  incident ticket.
- **Prolonged outage** – escalate to the infrastructure lead for broader
  coordination and resolution.
