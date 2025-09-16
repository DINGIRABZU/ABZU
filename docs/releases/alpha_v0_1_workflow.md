# Alpha v0.1 Workflow Gate

Alpha v0.1 establishes the first end-to-end readiness gate for the Spiral OS
stack. This workflow packages the build, verifies core health probes, and runs
the acceptance tests required to promote a candidate into the operator staging
loop documented in [alpha_v0_1_charter.md](../alpha_v0_1_charter.md) and the
[roadmap](../roadmap.md#alpha-v01-execution-plan).

## Prerequisites

- Complete the release preparation steps in
  [release_runbook.md](../release_runbook.md).
- Ensure the environment validation secrets (`GLM_API_URL`, `GLM_API_KEY`,
  `HF_TOKEN`) are exported or populated in `secrets.env`.
- Install Python build tooling (`python -m pip install build`) and make sure the
  repository root is clean (`git status` shows no pending changes).

## Build Packaging

Alpha promotion requires a reproducible artifact bundle.

1. Clean the previous build output:
   ```bash
   rm -rf dist/
   ```
2. Build the wheel artifact:
   ```bash
   python -m build --wheel
   ```
3. Archive the generated wheel and supporting manifests under `release/` and
   cross-check signatures per [release_process.md](../release_process.md).

Successful packaging verifies that the project metadata and dependencies are in
sync before health validation starts.

## Mandatory Health Checks

Run the following checks in order and address any failures before continuing.

1. **Environment and binary validation**
   ```bash
   scripts/check_requirements.sh
   ```
   Confirms required environment variables and binary dependencies are
   available.
2. **Self-healing and quarantine hygiene**
   ```bash
   python scripts/verify_self_healing.py --max-quarantine-hours 24 --max-cycle-hours 24
   ```
   Ensures the self-healing ledger recorded a successful cycle in the last
   24 hours and that no component remains in quarantine beyond the threshold.
3. **Connector heartbeat sweep** (optional but recommended)
   ```bash
   python scripts/health_check_connectors.py
   ```
   Validates `/health` endpoints for configured connectors before running
   acceptance tests. Supply connector URLs via `OPERATOR_API_URL`,
   `WEBRTC_CONNECTOR_URL`, and `PRIMORDIALS_API_URL` as needed.

## Acceptance Tests

### Minimal Spiral OS Boot Scripts

- Run the targeted Spiral OS initialization tests:
  ```bash
  pytest tests/test_start_spiral_os.py
  pytest tests/test_spiral_os.py
  ```
- These tests cover the boot diagnostics pipeline, ensure optional subsystems
  degrade gracefully, and confirm the CLI entry points align with
  [start_spiral_os.py](../../start_spiral_os.py).

### RAZAR Failover Validation

- Execute the integration suite for RAZAR failover ladders:
  ```bash
  pytest tests/integration/test_razar_failover.py
  ```
- The suite asserts the boot orchestrator escalates through Kimicho and R*Star,
  applies custom failover orders, and logs telemetry for
  `monitoring/razar_failover.json` dashboards.

### Nazarick / Memory Regression Sweep (Optional)

- Recommended smoke tests while the alpha gate is in flight:
  ```bash
  pytest tests/test_spiral_cortex_memory.py
  pytest tests/test_spiral_vector_db.py
  ```
- These confirm memory layer read/write paths continue to operate during boot
  and failover exercises.

## Automation

Use `scripts/run_alpha_gate.sh` to orchestrate the full workflow. The helper
script performs packaging, health checks, and test execution with structured
logging.

```bash
./scripts/run_alpha_gate.sh
```

Pass `--skip-build`, `--skip-health`, or `--skip-tests` to bypass individual
phases when rerunning investigations. The script exits with a non-zero status if
any phase fails and writes consolidated logs to `logs/alpha_gate/` for review.

## Version History

- 2025-03-01: Initial workflow capturing alpha gate packaging, health checks,
  and acceptance coverage.
