# Stage E PR & review checklist

Apply this checklist to Stage E beta-readiness changes and reviews to prevent
loops on sandbox-only verifications.

## Sandbox verification
- [ ] Highlight sandbox-only transport or heartbeat checks and cite [Codex sandbox constraints](../The_Absolute_Protocol.md#codex-sandbox-constraints).
- [ ] Include the `environment-limited: <reason>` skip text inside the PR summary and attach the matching `logs/stage_e/` bundle.
- [ ] Confirm transport dashboards or contract suites reference the sandbox hash recorded in roadmap and status trackers.

## Hardware follow-ups
- [ ] Note which hardware window (Stage D bridge, Stage G parity, or later) will replay the sandbox evidence and who owns the execution.
- [ ] Update the beta governance log with the hardware ticket or issue ID that tracks the follow-up.
- [ ] Ensure roadmap and [PROJECT_STATUS.md](../PROJECT_STATUS.md#stage-e-beta-readiness-snapshot) entries reference the queued hardware replay.

## Doctrine synchronization
- [ ] Cross-link updates in [roadmap.md](../roadmap.md#codex-sandbox-constraints) so reviewers see the sandbox policy callout.
- [ ] Refresh [doctrine_index.md](../doctrine_index.md) if any referenced checksum changed.
- [ ] Run `pre-commit run --files <modified docs>` before requesting review to capture lint and index updates.
