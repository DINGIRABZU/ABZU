# Stage D Execution Ladder

The Stage D bridge now runs against a four-rung execution ladder so weekly reviews can
trace exactly how sandbox evidence progresses toward hardware parity. Each rung links
to the readiness ledger, Codex sandbox policy, and the Stage F hardware replay plan
so owners inherit the prerequisites before advancing to the next checkpoint.【F:docs/readiness_ledger.md†L1-L41】【F:docs/The_Absolute_Protocol.md†L34-L116】【F:docs/stage_f_hardware_replay_plan.md†L3-L94】

## 1. Sandbox validation
- **Owners:** @qa-alliance · @release-ops
- **Focus:** Reconcile sandbox evidence across the Stage B rotation ledger, Stage C
  readiness bundle, and demo telemetry stub, confirming the owning squads and
  `environment-limited` skips recorded in the readiness ledger.
- **Exit criteria:**
  - All Stage D rows in the readiness ledger reflect current owners, sandbox caveats,
    and scheduled hardware follow-ups, with cross-links to the 2025-12-08 readiness
    review minutes.【F:docs/readiness_ledger.md†L16-L32】
  - Sandbox documentation mirrors the policy requirements from Codex sandbox
    constraints, including verbatim skip strings and pointers to the upcoming
    gate-runner replay window.【F:docs/The_Absolute_Protocol.md†L45-L116】
  - Stage F hardware replay plan inputs (merged Stage C bundle, Stage B ledger,
    Stage E transport snapshot) are staged and tagged for Stage D handoff so later
    rungs inherit consistent artifacts.【F:docs/stage_f_hardware_replay_plan.md†L56-L90】
- **Key references:** [Readiness ledger](readiness_ledger.md), [Codex sandbox constraints](The_Absolute_Protocol.md#codex-sandbox-constraints), [Stage F hardware replay plan](stage_f_hardware_replay_plan.md)

## 2. Simulation harness replay
- **Owners:** @ops-team · @neoabzu-core
- **Focus:** Execute the sandbox simulation harnesses (Stage C readiness replay,
  Stage B rotation drills) inside Codex, capturing parity diffs and validating that
  the ladder inputs remain reproducible before booking hardware time.
- **Exit criteria:**
  - Harness logs confirm every readiness ledger artifact replays cleanly in the
    sandbox with the same skip annotations recorded in the ledger.【F:docs/readiness_ledger.md†L34-L41】
  - Simulation outputs cite the sandbox policy requirements for deferred hardware
    steps, demonstrating that missing toolchains and credentials are documented per
    The Absolute Protocol.【F:docs/The_Absolute_Protocol.md†L55-L86】
  - Dry-run transcripts align with the staged automation flow in the hardware replay
    plan, including packaging of Stage B/Stage C/Stage E evidence and validation of
    tooling parity before hardware escalation.【F:docs/stage_f_hardware_replay_plan.md†L74-L88】
- **Key references:** [Readiness ledger](readiness_ledger.md), [Codex sandbox constraints](The_Absolute_Protocol.md#codex-sandbox-constraints), [Stage F hardware replay plan](stage_f_hardware_replay_plan.md)

## 3. Doctrine updates
- **Owners:** @release-ops · @qa-alliance · @documentation-guild
- **Focus:** Push refreshed doctrine (PROJECT_STATUS, roadmap, readiness memos) that
  captures the sandbox simulation results, ledger deltas, and pending hardware
  assignments before Stage D reviews.
- **Exit criteria:**
  - Status and roadmap entries link directly to the readiness ledger artifact table
    and highlight open sandbox caveats for Stage D owners.【F:docs/readiness_ledger.md†L16-L41】
  - Each doctrine update calls out the sandbox policy clause governing deferred
    checks, mirroring the `environment-limited` wording and hardware queue recorded
    in The Absolute Protocol.【F:docs/The_Absolute_Protocol.md†L61-L116】
  - Documentation enumerates the Stage F hardware replay plan prerequisites so Stage D
    checkpoints inherit the same evidence bundle, tooling checklist, and approval
    flow when submitting hardware requests.【F:docs/stage_f_hardware_replay_plan.md†L40-L94】
- **Key references:** [Readiness ledger](readiness_ledger.md), [Codex sandbox constraints](The_Absolute_Protocol.md#codex-sandbox-constraints), [Stage F hardware replay plan](stage_f_hardware_replay_plan.md)

## 4. Hardware prep
- **Owners:** @ops-team · @neoabzu-core · @qa-alliance
- **Focus:** Reserve the gate-runner slot, finalize tooling parity, and assemble the
  hardware replay packet so Stage D execution can promote sandbox evidence with
  verifiable lineage.
- **Exit criteria:**
  - Readiness ledger entries are updated with the confirmed hardware reservation ID
    and planned evidence uploads so auditors can trace the bridge closure.【F:docs/readiness_ledger.md†L34-L41】
  - Hardware preparation notes enumerate the sandbox policy obligations—tooling
    gaps, credential injections, and approval trail—mapped to the scheduled replay
    window.【F:docs/The_Absolute_Protocol.md†L70-L116】
  - The Stage F hardware replay plan checklist is satisfied through staging sandbox
    artifacts, validating tooling parity, and capturing approval templates ready for
    signature during the hardware run.【F:docs/stage_f_hardware_replay_plan.md†L67-L128】
- **Key references:** [Readiness ledger](readiness_ledger.md), [Codex sandbox constraints](The_Absolute_Protocol.md#codex-sandbox-constraints), [Stage F hardware replay plan](stage_f_hardware_replay_plan.md)

> [!NOTE]
> Weekly Stage D reviews should walk the rungs in order, closing each exit
> criterion before progressing, and log any blocked items back into the readiness
> ledger with the matching sandbox policy citation so the ladder remains auditable.
