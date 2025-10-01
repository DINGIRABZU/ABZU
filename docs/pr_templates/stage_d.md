# Stage D PR & review checklist

Use this template when preparing Stage D bridge changes or reviews. It keeps
sandbox evidence, hardware follow-ups, and doctrine updates in sync.

## Sandbox verification
- [ ] Call out every sandbox-only task and cite [Codex sandbox constraints](../The_Absolute_Protocol.md#codex-sandbox-constraints).
- [ ] Copy the exact `environment-limited: <reason>` strings from test skips into the PR summary and linked evidence bundles.
- [ ] Link to the supporting `logs/stage_c/` or `logs/stage_d/` bundle demonstrating the sandbox transcript.

## Hardware follow-ups
- [ ] Queue hardware reruns in the bridge ledger (`logs/stage_d/` or Stage G plan) and note the owner responsible for replaying the sandbox artifact.
- [ ] Reference the roadmap entry that schedules the hardware slot so reviewers see when deferred evidence will land.
- [ ] Confirm the readiness packet or roadmap entry that inherits the replayed hashes once hardware execution completes.

## Doctrine synchronization
- [ ] Update [roadmap.md](../roadmap.md#codex-sandbox-constraints) and [PROJECT_STATUS.md](../PROJECT_STATUS.md#stage-d-bridge-snapshot) with matching sandbox notes.
- [ ] Refresh [doctrine_index.md](../doctrine_index.md) if any tracked checksum changed.
- [ ] Re-run `pre-commit run --files <modified docs>` to trigger documentation linters before requesting review.
