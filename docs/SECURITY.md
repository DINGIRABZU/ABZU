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
| `AiRstar`  | `AIRSTAR_API_KEY`     | Rotate every 30 days; revoke and replace after any escalation to Microsoft support. | Same storage rule as above. The key may be dual-homed in Azure Key Vault but must be injected as an environment variable at launch. | Same sandbox as above; audit log entry records every invocation. |
| `rStar`    | `RSTAR_API_KEY`       | Rotate every 30 days; rotate in lockstep with `AIRSTAR_API_KEY` when the services share a tenant. | Store alongside the AiRstar key with identical retention policies. Export only to the invocation worker. | Same sandbox guardrails; exit codes are recorded and failures trigger fallback repair logic. |

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
