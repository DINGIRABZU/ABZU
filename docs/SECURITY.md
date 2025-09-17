# Security Overview

## Remote Agent Credentials

The RAZAR remediation pipeline can delegate failure analysis to several hosted
agents. Each agent now **must** source its API key from a dedicated environment
variable; configuration tokens and fallback names are ignored. The loader in
`razar/ai_invoker.py` validates the variables and fails fast with an
`AgentCredentialError` when a required secret is missing or empty.

| Agent name | Environment variable | Rotation cadence | Storage & handling | Sandbox guardrails |
| ---------- | -------------------- | ---------------- | ------------------ | ------------------ |
| `kimi2`    | `KIMI2_API_KEY`       | Rotate every 30 days or immediately after operator turnover. | Keep the key in the sealed secrets store; export it to the runtime environment only for the agent process. Never commit it to disk, logs, or patch archives. | Spawned worker limited to 90s CPU time and ~512 MB RAM; outbound network constrained to the configured endpoint. |
| `Air Star` | `AIRSTAR_API_KEY`     | Rotate every 30 days; revoke and replace after any escalation to Microsoft support. | Same storage rule as above. The key may be dual-homed in Azure Key Vault but must be injected as an environment variable at launch. | Same sandbox as above; audit log entry records every invocation. |
| `rStar`    | `RSTAR_API_KEY`       | Rotate every 30 days; rotate in lockstep with `AIRSTAR_API_KEY` when the services share a tenant. | Store alongside the Air Star key with identical retention policies. Export only to the invocation worker. | Same sandbox guardrails; exit codes are recorded and failures trigger fallback repair logic. |

### Rotation & Storage Policy

- Secrets live exclusively inside the platform secrets manager. Deployment
  pipelines inject them into the environment of the calling service and never
  persist them to disk.
- Rotation cadence defaults to 30 days for all three services. Emergency
  rotation is mandatory whenever a key is exposed, an operator leaves the
  rotation group, or the vendor requests renewal.
- The worker process wipes its environment after the invocation. Patch logs and
  telemetry include only the environment variable **names**, never the values.
- The agent loader refuses blank strings, placeholder tokens, or unset
  variables; these conditions surface as explicit errors in logs and metrics.

### Credential Rotation Workflow

- Maintain the sanitized rotation manifests under `secrets/`. Each JSON or
  YAML file must list the agent `name`, the environment variable that carries
  the credential, and (when applicable) a `config_path` override that points to
  a staging copy of `config/razar_ai_agents.json`.
- Initiate the rotation every 30 days (or immediately after an exposure) by
  running a **dry run** to stage new placeholders and confirm cache invalidation:

  ```bash
  python scripts/rotate_remote_agent_keys.py --secrets-dir secrets --dry-run
  ```

  The helper reads the manifests, generates non-secret placeholder values, and
  asserts that `invalidate_agent_config_cache` forces `ai_invoker` to reload
  the updated roster.
- Seek two-person approval before applying changes: the Security Lead approves
  the credential update and the RAZAR service owner confirms that the rotation
  aligns with the current incident state. Record both approvals (and the new
  placeholder identifiers) in the active incident or change-management ticket.
- After approval, apply the placeholders in a sandbox environment:

  ```bash
  python scripts/rotate_remote_agent_keys.py --secrets-dir secrets --apply
  pytest tests/test_credential_rotation.py
  ```

  Export the placeholders to the sandbox runtime and trigger a smoke handover to
  ensure the remote agent responds before propagating the secrets manager
  update to production.
- Once the sandbox validation passes, promote the credential update through the
  deployment pipeline. Never copy placeholders or real tokens into Git history;
  store the audit record exclusively in the ticketing system.

### Invocation Sandbox

Every external handover executes inside a dedicated, resource-constrained
worker process.

- CPU execution is capped at 90 seconds. Processes exceeding the limit are
  terminated and recorded as sandbox violations.
- Memory allocations are limited to approximately 512 MB to prevent runaway
  models from exhausting host resources.
- The worker inherits only the minimal environment required for the target
  agent and cannot persist files outside of the temporary patch backup
  directory.
- When the sandbox aborts an invocation, the orchestrator logs the exit code,
  records the failure in metrics, and falls back without applying untrusted
  patches.
