# Operator Protocol

Defines endpoints for operators to dispatch commands and upload assets to agents.

## Authentication

All requests require an `Authorization: Bearer <token>` header. Unauthorized requests return `401`.

## `/operator/command`

`POST /operator/command` dispatches a command to an agent.

```bash
curl -X POST localhost:8000/operator/command \
  -H 'Authorization: Bearer <token>' \
  -d '{"operator":"crown","agent":"razar","command":"status"}'
```

**Body Fields**
- `operator` – issuing operator
- `agent` – target agent
- `command` – directive string

The response contains `result` and may include `escalation_required`.

## `/operator/upload`

`POST /operator/upload` sends an asset to an agent.

```bash
curl -X POST localhost:8000/operator/upload \
  -H 'Authorization: Bearer <token>' \
  -F 'operator=crown' \
  -F 'agent=razar' \
  -F 'file=@intel.jpg'
```

Supports multipart file uploads or base64-encoded payloads.

## Escalation

If a request returns `escalation_required: true` or a `5xx` status, the operator must alert a human overseer and halt automated retries. Include the last command payload in the escalation report.
