# Release Runbook

## Boot Order
1. Start the RAZAR runtime manager to initialize the environment and orchestrate service startup.
2. Launch core services in priority order once RAZAR reports readiness.
3. Bring up auxiliary modules after core services pass their readiness checks.

## Health Checks
- Monitor `/health` endpoints for each service and confirm they return status `healthy`.
- Use `scripts/vast_check.py` to aggregate system health and route metrics to the logging pipeline.
- Halt the rollout if any component reports degraded status or fails to respond.

## GPU and Driver Validation
- Run `nvidia-smi` to verify the GPU is detected and drivers match the supported version.
- Execute `python scripts/check_gpu.py` (if available) to confirm CUDA visibility and device memory.
- Abort deployment if GPU tests fail or drivers are outdated.

## Rollback Steps
1. Stop the affected service and review `logs/razar.log` for the last stable component.
2. Restore from the most recent snapshot or container image.
3. Restart services in boot order, validating health checks before advancing.
4. Document the rollback and remediation steps.

## Sign-Off Checklist
Confirm completion of the following before declaring the release complete. Refer to [The Absolute Protocol](The_Absolute_Protocol.md) for the full repository rules and mandatory sign-off steps.

- [ ] Environment prepared and required secrets configured.
- [ ] `pre-commit run --files docs/release_runbook.md docs/INDEX.md` executed with no failures.
- [ ] Key documents verified with `scripts/verify_doc_hashes.py`.
- [ ] Tests executed and coverage meets minimum thresholds.
- [ ] Changelog updated and release tag created.

