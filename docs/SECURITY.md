# Security Overview

## Remote Agent Credentials

The RAZAR remediation pipeline can delegate failure analysis to several hosted
agents. Each agent requires an API key that must be injected via environment
variables at runtime. The loader in `razar/ai_invoker.py` automatically maps
agent names to their corresponding secrets.

| Agent name | Accepted secret variables | Notes |
| ---------- | ------------------------- | ----- |
| `kimi2`    | `KIMI2_API_KEY`, `KIMI2_TOKEN` | Standard MoonshotAI Kimi‑K2 deployment. |
| `AiRstar` / `rStar` | `RSTAR_API_KEY`, `RSTAR_TOKEN`, `AIRSTAR_API_KEY`, `AIRSTAR_TOKEN` | `AiRstar` and `rStar` are aliases for the same Microsoft-hosted service. Either prefix is accepted. |

Only one variable in each column is required; if multiple variables are set
for the same agent the first populated value in the list is used. Secrets are
never persisted to disk and are only forwarded to the active agent during the
sandboxed invocation window.

## Sandboxed Delegation

All remote handovers now execute inside a constrained worker process. The
sandbox enforces:

- A CPU wall-clock timeout of 90 seconds for the external invocation.
- Memory limits of approximately 512 MB to prevent runaway allocations.

If the sandbox terminates the agent early—due to the timeout or resource
limits—the failure is logged and the orchestrator falls back without applying
untrusted patches.
