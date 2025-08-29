# Co-creation Escalation

Outlines how RAZAR, Crown, and the human operator respond when automated coordination stalls.

## RAZAR Requests Crown Assistance
- RAZAR first attempts self‑recovery for failed services.
- If a component remains unhealthy after two retry cycles or misses a health check for 60 seconds, RAZAR asks Crown to intervene.
- Crown dispatches the appropriate servant agent or applies a fallback configuration.

## Operator Escalation Thresholds
- Crown escalates to the operator when automated fixes fail or when three consecutive requests from RAZAR for the same component occur within ten minutes.
- Critical services offline for more than five minutes trigger immediate operator notification.
- Operator commands must acknowledge receipt before Crown resumes automated control.

## Logging Requirements
- **Tier 1 – Crown Assistance:** RAZAR records the failing component and retry attempts in `logs/razar.log` and adds a warning entry to the monitoring stream.
- **Tier 2 – Operator Escalation:** Crown writes an audit entry to `logs/operator.log` including timestamps, component identifiers, and the reason for escalation. The operator’s response is appended once received.
- All logs must retain timestamps and correlation IDs so incidents can be traced across tiers.
