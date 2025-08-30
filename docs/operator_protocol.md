# Operator Protocol

Defines how operator commands and uploads are issued and validated across the system.

## Endpoint `/operator/command`

Sends a JSON payload describing the action to execute. Requests must use `POST` and include authentication headers.

## Endpoint `/operator/upload`

Uploads one or more files using `multipart/form-data`. Each request must include a `files` field and may include an optional `metadata` field containing JSON. Crown saves files under `uploads/` and forwards the metadata to RAZAR.

## WebRTC Channels

The Nazarick Web Console establishes a WebRTC connection to stream avatar output. Clients may request:

- **Video** – avatar frames.
- **Audio** – PCM/WAV audio.
- **Data** – arbitrary binary payloads.

Only the requested tracks are attached during negotiation. When media negotiation fails the session falls back to data-channel messages so command traffic continues.

## Roles and Permission Checks

Crown authorizes requests against `permissions.yml`. Only identities with the `operator` role may invoke this endpoint. Invalid or missing roles return a `403` response.

## Authentication

All operator endpoints and WebRTC signalling requests require an `Authorization` header containing a JWT or API token. Requests without valid credentials are rejected with `401`.

## Rate Limits

Crown enforces per-operator limits:

- 60 command requests per minute.
- 5 upload requests per minute.
- 1 active WebRTC session.

Exceeding a limit returns `429 Too Many Requests`.

## Fallback Rules

- If audio or video streaming cannot be established, the WebRTC session continues over the data channel.
- When RAZAR is unavailable or rejects a command, Crown logs the failure and surfaces the error to the operator for escalation.

## Crown Relay to RAZAR

After validation Crown forwards the command to RAZAR's control loop. RAZAR executes the action and returns the result, which Crown relays back to the caller.

## Interaction Logging

As defined in [The Absolute Protocol](The_Absolute_Protocol.md#razar-crown-operator-interaction-logging),
all exchanges between RAZAR, Crown, and the Operator are logged to
[`../logs/interaction_log.jsonl`](../logs/interaction_log.jsonl) with:

- timestamp
- initiator
- action or request
- response summary

## Release Cadence

Minor updates to the Operator Protocol are targeted for release each month, with patch revisions issued as needed for urgent fixes or compatibility adjustments.

## Escalation Path

RAZAR and Crown follow the [Co-creation Escalation](co_creation_escalation.md) guide when automated recovery fails. It defines when RAZAR requests Crown assistance, when Crown alerts the operator, and how each step is logged.
