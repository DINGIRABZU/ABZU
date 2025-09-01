# Operator Protocol

Defines the interfaces and logging expectations for direct operator interactions.

## Endpoints

- **`POST /operator/command`** – forwards structured instructions for RAZAR to execute. The payload must include an `action` field and optional `parameters`. Responses echo the action and report success or failure.
- **`POST /operator/upload`** – accepts auxiliary files and arbitrary JSON metadata. The body is multipart form data with one or more `files` parts and a `metadata` field; successful uploads return stored paths merged into the metadata payload.
- **`POST /call`** – negotiates a WebRTC session for real‑time data, audio, and video exchange. Clients send an SDP offer and receive an SDP answer in the response.
- **`GET /story/log`** – returns stored narratives and memory metadata.
- **`GET /story/stream`** – streams narratives and memory metadata as JSON lines.

See the [`webrtc`, `operator_upload`, `crown_ws`, and `narrative_api` entries in the Connector Index](connectors/CONNECTOR_INDEX.md) for versioning and implementation details.

## Authentication

All requests require an `Authorization` header with a Bearer token carrying the `operator` role. Tokens are JWTs issued by the Crown identity service; RAZAR rejects commands when the role is missing or insufficient.

## Rate Limits

`POST /operator/command` is limited to **60 requests per minute** per operator. `POST /operator/upload` allows **20 uploads per minute**. Exceeding either limit results in `429 Too Many Requests`.

## Narrative Retrieval

Use `GET /story/log` to fetch stored narratives with memory metadata. `GET /story/stream` emits the same data as JSON lines for subscription-style consumption.

## WebRTC Channels

The WebRTC connector offers up to three channels:

- **Data channel** – streams encoded audio segments or control messages.
- **Audio track** – forwards live microphone input when enabled.
- **Video track** – streams avatar video frames.

Clients authenticate with a JWT and should close peers when finished. Disabled tracks are omitted from the session description and may fall back to `POST /operator/upload`.

## Media Fallback

Real‑time audio and video streams are optional. When disabled via connector configuration or if media tracks fail to initialise, clients fall back to data‑only interaction. Operators should then upload pre‑recorded media using `POST /operator/upload`, which Crown relays to RAZAR alongside the provided metadata.

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
