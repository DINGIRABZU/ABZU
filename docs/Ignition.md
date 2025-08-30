# Ignition

RAZAR coordinates system boot and records runtime health. Components are grouped by priority so operators can track startup order and service status. See [The Absolute Protocol](The_Absolute_Protocol.md) for ignition stage requirements and [Ignition Map](ignition_map.md) for component stages.

## Priority 0
| Order | Component | Health Check | Status |
| --- | --- | --- | --- |
| 0 | RAZAR Startup Orchestrator | Confirm the environment hash and orchestrator heartbeat. | ⚠️ |
| 1 | Environment Builder | Ensure `.razar_venv` exists with required layers. | ⚠️ |
| 2 | Runtime Manager | Verify `logs/razar_state.json` records the last component. | ⚠️ |
| 3 | Health Checks | Ping Prometheus metrics endpoint. | ⚠️ |
| 4 | Quarantine Manager | Confirm `quarantine/` and `docs/quarantine_log.md` exist. | ⚠️ |
| 5 | Documentation Sync | Check `docs/INDEX.md` regenerated. | ⚠️ |
| 6 | Checkpoint Manager | Ensure `logs/razar_state.json` includes `last_component`. | ⚠️ |
| 7 | Crown Link | Validate `logs/razar_crown_dialogues.json` present. | ⚠️ |
| 8 | Adaptive Orchestrator | Check `logs/razar_boot_history.json` captured metrics. | ⚠️ |
| 9 | Co-creation Planner | Ensure `logs/razar_cocreation_plans.json` saved a plan. | ⚠️ |

## Priority 1
| Order | Component | Health Check | Status |
| --- | --- | --- | --- |
| 10 | Memory Store | - | ⚠️ |

## Priority 2
| Order | Component | Health Check | Status |
| --- | --- | --- | --- |
| 11 | Chat Gateway | - | ⚠️ |
| 12 | CROWN LLM | - | ⚠️ |
| 13 | Vision Adapter | - | ⚠️ |
| 14 | Inanna AI | Confirm `/ready` endpoint responds on `INANNA_PORT`. | ⚠️ |

## Priority 3
| Order | Component | Health Check | Status |
| --- | --- | --- | --- |
| 15 | Audio Device | - | ⚠️ |

## Priority 4
| Order | Component | Health Check | Status |
| --- | --- | --- | --- |
| 16 | Avatar | - | ⚠️ |

## Priority 5
| Order | Component | Health Check | Status |
| --- | --- | --- | --- |
| 17 | Video | - | ⚠️ |

## Regeneration
RAZAR monitors component events and rewrites this file whenever a priority or health state changes. Status markers update to:

- ✅ healthy
- ⚠️ starting or degraded
- ❌ offline

This keeps the ignition sequence in version control so operators can audit boot cycles.
