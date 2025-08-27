# Ignition

RAZAR coordinates system boot and records runtime health. Components are grouped by priority so operators can track startup order and service status.

## Priority 0 – Orchestrator
| Order | Component | Health Check | Status |
| --- | --- | --- | --- |
| 0 | RAZAR Startup Orchestrator | `razar --status` | ⚠️ |

## Priority 1 – Persistence
| Order | Component | Health Check | Status |
| --- | --- | --- | --- |
| 1 | Memory Store | `curl http://memory/ready` | ⚠️ |

## Priority 2 – Gateways
| Order | Component | Health Check | Status |
| --- | --- | --- | --- |
| 2 | Chat Gateway | `curl http://chat/health` | ⚠️ |
| 3 | CROWN LLM | dummy prompt round‑trip | ⚠️ |

## Priority 3 – Audio
| Order | Component | Health Check | Status |
| --- | --- | --- | --- |
| 4 | Audio Device | loopback test | ⚠️ |

## Priority 4 – Avatar
| Order | Component | Health Check | Status |
| --- | --- | --- | --- |
| 5 | Avatar | frame render ping | ⚠️ |

## Priority 5 – Video
| Order | Component | Health Check | Status |
| --- | --- | --- | --- |
| 6 | Video | stream probe | ⚠️ |

## Regeneration
RAZAR monitors component events and rewrites this file whenever a priority or health state changes. Status markers update to:

- ✅ healthy
- ⚠️ starting or degraded
- ❌ offline

This keeps the ignition sequence in version control so operators can audit boot cycles.

