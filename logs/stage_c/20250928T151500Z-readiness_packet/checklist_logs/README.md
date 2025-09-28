# Stage C Checklist Evidence

This directory consolidates Stage C1 exit checklist metadata for the 2025-09-25 rehearsal.
The raw sandbox exports live on the release-ops share and are not mirrored inside the Codex
sandbox; the JSON stub records their locations and the environment-limited skips called out in
`docs/absolute_protocol_checklist.md`.

- `stage_c1_exit_checklist_summary.json` — high-level summary with the referenced log paths,
  environment-limited blockers, and next actions for hardware follow-up.
- `docs/absolute_protocol_checklist.md` — canonical checklist with inline notes describing why
  pytest coverage and build packaging remain deferred.

When new checklists run, add a sibling JSON file and update this index so the readiness packet
mirrors the release-ops evidence vault.
