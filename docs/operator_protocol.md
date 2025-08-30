# Operator Protocol

Defines the interfaces and logging expectations for direct operator interactions.

## Endpoints

- **`POST /operator/command`** – forwards structured instructions for RAZAR to execute. The payload must include an `action` field and optional `parameters`. Responses echo the action and report success or failure.
- **`POST /operator/upload`** – accepts auxiliary files referenced in later commands. The body is multipart form data with a `file` part; successful uploads return a storage identifier.

See the [`operator_api` entry in the Connector Index](connectors/CONNECTOR_INDEX.md#operator_api) for versioning and implementation details.

## Authentication

All requests require an `Authorization` header with a Bearer token carrying the `operator` role. RAZAR rejects commands when the role is missing or insufficient.

## Rate Limits

`POST /operator/command` is limited to **60 requests per minute** per operator. `POST /operator/upload` allows **20 uploads per minute**. Exceeding either limit results in `429 Too Many Requests`.

## Storage Paths

Uploaded files are stored under `uploads/<operator>/`. The API response returns the relative paths, and Crown forwards both the paths and supplied metadata to RAZAR.

## Escalation Rules

1. RAZAR handles standard commands and file ingests.
2. If RAZAR cannot fulfil a request or detects anomalous behavior, it relays the command and context to Crown for arbitration.
3. Crown may escalate back to the human operator for confirmation or deny the action. All escalations are recorded in the mission-brief log.

## Mission‑brief Logging

Every handshake produces a JSON mission brief under `logs/mission_briefs/` capturing the initiating party, action summary, and final acknowledgement. Example:

```json
{
  "timestamp": "2025-09-02T12:00:00Z",
  "initiator": "operator",
  "action": "status_check",
  "escalated_to": "Crown",
  "acknowledgement": {
    "status": "accepted",
    "relay": "RAZAR"
  }
}
```

These logs enable auditors to trace operator involvement and Crown's relay to RAZAR.
