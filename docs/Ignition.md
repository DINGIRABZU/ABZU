# Ignition

RAZAR coordinates system boot and records runtime health. Components are grouped by priority so operators can track startup order and service status.

## Priority 0
| Order | Component | Health Check | Status |
| --- | --- | --- | --- |
| 0 | RAZAR Startup Orchestrator | Confirm the environment hash and orchestrator heartbeat. | ⚠️ |

## Priority 1
| Order | Component | Health Check | Status |
| --- | --- | --- | --- |
| 1 | Memory Store | - | ⚠️ |

## Priority 2
| Order | Component | Health Check | Status |
| --- | --- | --- | --- |
| 2 | Chat Gateway | Probe `/chat/health` and watch latency. | ⚠️ |
| 3 | CROWN LLM | Send a dummy prompt and inspect response time. | ⚠️ |

## Priority 3
| Order | Component | Health Check | Status |
| --- | --- | --- | --- |
| 4 | Audio Device | Run an audio loopback test. | ⚠️ |

## Priority 4
| Order | Component | Health Check | Status |
| --- | --- | --- | --- |
| 5 | Avatar | Verify avatar frame rendering. | ⚠️ |

## Priority 5
| Order | Component | Health Check | Status |
| --- | --- | --- | --- |
| 6 | Video | Probe the video stream endpoint. | ⚠️ |

## Regeneration
RAZAR monitors component events and rewrites this file whenever a priority or health state changes. Status markers update to:

- ✅ healthy
- ⚠️ starting or degraded
- ❌ offline

This keeps the ignition sequence in version control so operators can audit boot cycles.
