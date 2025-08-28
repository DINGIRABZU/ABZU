# RAZAR Agent

## Pre-Creation Mandate
RAZAR provisions a clean environment before any servant boots. It resets temporary directories, verifies configuration files, and ensures secrets and caches are sanitized.

## Priority Boot Order
RAZAR starts services according to an ordered priority list. Each component exposes health and readiness probes; RAZAR waits for green checks before advancing. Components that fail checks are isolated and quarantined to `quarantine/` with logs for review.

## CROWN Handshake
Once core services are healthy, RAZAR initiates a handshake with the CROWN LLM. The agent exchanges identity tokens, registers servant models, and confirms message routes so downstream agents can communicate through CROWN.

---

Backlinks: [Nazarick Agents](nazarick_agents.md) | [System Blueprint](system_blueprint.md)
