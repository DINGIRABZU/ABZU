# Documentation Protocol

Standard workflow for updating documentation and guides.

1. **Check for applicable `AGENTS.md` instructions** to understand directory-specific conventions.
2. **Follow the [Arcade Theme Style Guide](style_guides/arcade_theme.md)** for color and typography rules.
3. **Update all related documents** whenever a component or guide changes to keep information synchronized.
4. **Sync `docs/system_blueprint.md`** whenever components or documentation change to keep the architectural overview current.
5. **Document APSU sequence placement** for new components and migrations, linking to relevant diagrams such as [`blueprint_spine.md`](blueprint_spine.md) or [`system_blueprint.md`](system_blueprint.md). See the [Rust migration rules](The_Absolute_Protocol.md#rust-migration-rules) for guidance.
6. **Ensure `docs/INDEX.md` stays current.** The `doc-indexer` pre-commit hook regenerates the index
   automatically when files in `docs/` change, skipping `node_modules`, `dist`, and `build`
   directories to avoid indexing generated artifacts.
7. **Validate changes with** `pre-commit run --files <changed_files>` **before committing.**
8. **Use traceable commit messages** that capture the rationale for changes and reference affected documents.
9. **When bumping component or dependency versions:** update the relevant entries in
   `requirements.txt` and lockfiles, run `python scripts/validate_components.py` to ensure
   versions align, then execute `docs/build_docs.sh` to regenerate indexes (documentation index,
   API docs, component status) and verify links. Finally, run `python scripts/validate_docs.py`
   to confirm registry versions and cross-links remain in sync.
10. **Run `python scripts/verify_docs_up_to_date.py`** to confirm the doctrine index timestamps and
    feature references are current before submitting a pull request.

### Codex sandbox constraints

Codex-hosted updates must spell out which verification steps ran inside the sandbox and which remain
hardware-only so doctrine readers inherit the right expectations:

- **Sandbox-only tasks.** GPUs, DAW integrations, FFmpeg exports, and Neo-APSU parity drills stay in
  dry-run mode until the Stage D/E bridge rehearsals or the Stage G hardware slot executes them on the
  designated runner. Record those items as sandbox-only in the doc text and link back to
  [The Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints) for the canonical rule set.
- **Environment-limited tagging.** Mirror the exact `environment-limited: <reason>` phrasing from test
  skips inside change logs, readiness packets, and doc callouts so auditors can trace why a result was
  deferred. Cite the evidence bundle path (`logs/<gate>/<timestamp>/`) and owner responsible for closing
  the loop whenever a page documents a sandbox skip.
- **Hardware replay narrative.** Reference the follow-up slot in [roadmap.md](roadmap.md#stage-g-sandbox-to-hardware-bridge-validation)
  or [PROJECT_STATUS.md](PROJECT_STATUS.md#stage-d-bridge-snapshot) when you defer migration evidence. The
  documentation update must state which hardware window will replay the sandbox output and which ledger
  (Stage D/E bridge, Stage G parity) will capture the replayed hashes once complete.

- **Latest readiness packet alignment.** Tie Codex sandbox notes to the 2025-11-05 Stage A gate runs and the 2025-12-05 Stage B
  rehearsals so reviewers inherit the most recent `environment-limited` warnings. Quote the exact skip strings recorded in the
  Stage A bootstrap/replay/gate shakeout summaries and the Stage B memory proof/connector rotation exports when updating docs or
  readiness packets.【F:logs/stage_a/20251105T170000Z-stage_a1_boot_telemetry/summary.json†L1-L41】【F:logs/stage_a/20251105T172000Z-stage_a3_gate_shakeout/summary.json†L1-L62】【F:logs/stage_b/20251205T142355Z-stage_b1_memory_proof/summary.json†L1-L63】【F:logs/stage_b/20251205T160210Z-stage_b3_connector_rotation/summary.json†L1-L129】
- **Review minutes traceability.** Whenever a cross-team readiness review runs, store the minutes beside the readiness packet
  and reference them when describing sandbox limits or hardware follow-ups. The 2025-12-08 minutes document the hardware replay
  window, attendee decisions, and the mandate to mirror `environment-limited` tags across PRs and doctrine updates.【F:logs/stage_c/20251205T193000Z-readiness_packet/review_minutes.md†L1-L39】

> [!IMPORTANT]
> **Document environment-limited skips.** Follow the guardrails in [The Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints) whenever the Codex sandbox blocks dependencies or hardware (GPU-only flows, DAW toolchains, connector credentials). Call out the "environment-limited" skip in both the change log excerpt and PR summary, mirroring the skip reason used in tests or gate scripts so reviewers can trace deferred validations. Reference the sandbox-to-hardware bridge workflow in [roadmap.md](roadmap.md#stage-g-sandbox-to-hardware-bridge-validation) when queuing hardware reruns so documentation stays aligned with the gate owner schedule.
> Change logs and readiness packets must also state when results rely on stubs or deferred hardware validation, naming the affected step, the rehearsal host that will close the gap, and the sign-off trio documented in [The Absolute Protocol](The_Absolute_Protocol.md#sandbox-to-hardware-rehearsal-bridge).
> Reference the latest Stage C1 exit checklist summary and readiness review minutes when documenting these skips so every doctrine update points to the gate-runner-02 hardware window and the owning leads recorded in the evidence bundle.【F:logs/stage_c/20250930T210000Z-stage_c1_exit_checklist/summary.json†L1-L35】【F:logs/stage_c/20251001T010101Z-readiness_packet/review_minutes.md†L14-L44】

Document updates must also cite the aggregated readiness packet (`logs/stage_c/20251001T010101Z-readiness_packet/`) whenever summarizing sandbox vs hardware status so reviewers inherit the same MCP parity artifacts and scheduled hardware reruns traced in doctrine ledgers.【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L185】【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L222】

When referencing the refreshed Stage C readiness bundle (2025-12-05), include the hardware follow-up slate from the review minutes and point to the sandbox handshake/heartbeat artifacts logged alongside the packet so auditors can cross-check the pending MCP evidence.【F:logs/stage_c/20251205T193000Z-readiness_packet/readiness_bundle.json†L1-L33】【F:logs/stage_c/20251205T193000Z-readiness_packet/review_minutes.md†L1-L39】【F:logs/stage_c/20251205T193000Z-readiness_packet/mcp_artifacts/handshake.json†L1-L12】

11. **Run `python scripts/check_connectors.py`** whenever files in `connectors/` or related modules change. The script fails on placeholder markers or missing MCP adoption. Every connector update must also refresh the corresponding documentation with protocol and heartbeat details.

12. **Stage G doctrine synchronization:** When updating sandbox-to-hardware bridge evidence, align `docs/roadmap.md#stage-g`, `docs/PROJECT_STATUS.md#stage-g`, and `docs/The_Absolute_Protocol.md#stage-gate-alignment` so hardware owners, rollback drills, and approvals stay in lockstep. Reference the latest Stage G parity bundles (`logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/`, `logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/`) and re-run `pre-commit run --files <changed docs>` to refresh doctrine hooks and the index entries they update.【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/summary.json†L1-L13】【F:logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/summary.json†L1-L13】

