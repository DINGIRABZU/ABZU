# Ignition Sequence Protocol

Defines the required logging checkpoints and escalation flow during the
system boot sequence.

## Mandatory Logging Points

- **Boot start** – record timestamp and environment hash in
  `logs/razar_boot_history.json`.
- **Component activation** – log each component start and health check to
  `logs/razar_state.json`.
- **Quarantine events** – append affected component IDs and reasons to
  [`quarantine_log.md`](quarantine_log.md).
- **Sequence completion** – write final status and coverage snapshot to
  `logs/ignition_summary.json`.

## Operator Escalation Path

1. **Automated retry** – RAZAR attempts a restart up to three times.
2. **Crown notification** – persistent failures trigger a Crown alert via
   `/operator/command`.
3. **Operator response** – operators consult the
   [Recovery Playbook](recovery_playbook.md) and resolve outstanding
   issues.
4. **Emergency escalation** – unresolved faults escalate to the
   [Co-creation Escalation](co_creation_escalation.md) protocol for
   manual intervention and post‑mortem logging.

