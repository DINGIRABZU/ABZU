# Stage B Heartbeat Payload

The Neo-APSU Stage B rehearsal emits a canonical heartbeat payload through the MCP
`/heartbeat` endpoint. The template in
[`connectors/neo_apsu_connector_template.py`](../../connectors/neo_apsu_connector_template.py)
applies baseline metadata, validates overrides, and guarantees that the gateway
receives the telemetry required by doctrine.

## Canonical Fields

| field | type | required | default | notes |
| --- | --- | --- | --- | --- |
| `chakra` | string | yes | `"neo"` | Must be a non-empty string. Custom values are accepted when present in the payload and are validated before emission. |
| `cycle_count` | integer | yes | `0` | Must be a non-negative integer. Boolean values are rejected even when numerically castable. |
| `context` | string | yes | `"stage-b-rehearsal"` | The connector locks heartbeat telemetry to the Stage B rehearsal context and will raise if any other value is supplied. |
| `credential_expiry` | string (`date-time`) | yes | sourced from MCP session | Derived from the handshake response (`session.credential_expiry` or `session.expires_at`). A manual override may be provided, but the value must be a valid ISO-8601 timestamp. |
| `emitted_at` | string (`date-time`) | yes | current UTC timestamp | Automatically set when omitted so the payload always carries an emission time in ISO-8601 `Z` form. |

Additional telemetry fields—such as `status`, `latency_ms`, or channel-specific
metadata—may be included. The schema allows extra properties so operators can
extend diagnostics without breaking validation.

## Override Rules

1. **Defaults first.** `_prepare_heartbeat_payload` merges payload fields with the
   canonical metadata so every heartbeat contains the baseline `chakra`,
   `cycle_count`, and `context` values when operators provide partial updates.
2. **Strict validation.** The helper enforces a non-empty string for `chakra`, a
   non-negative integer for `cycle_count`, and a literal `stage-b-rehearsal`
   context. Any mismatch raises before the HTTP request is attempted.
3. **Credential expiry required.** The heartbeat must carry a `credential_expiry`
   timestamp. The connector first inspects the handshake `session` object for a
   `credential_expiry` or `expires_at` field and falls back to an explicit
   override parameter. If neither is available the emission is aborted.
4. **ISO-8601 timestamps.** Both `credential_expiry` and `emitted_at` are
   normalised to `YYYY-MM-DDTHH:MM:SSZ`. Supplying naive datetimes or alternate
   offsets causes validation to fail before telemetry is posted.

These rules ensure that Stage B rehearsals advertise their authentication window
and cycle alignment on every beat, allowing downstream monitors to catch drift
immediately.

## JSON Schema

The Stage B heartbeat schema lives in
[`schemas/mcp_heartbeat_payload.schema.json`](../../schemas/mcp_heartbeat_payload.schema.json)
and mirrors the validation logic enforced by the connector. It models the
required fields, ISO-8601 formats, and allows custom diagnostics via additional
properties.

## Sample Payload

```json
{
  "chakra": "neo",
  "cycle_count": 12,
  "context": "stage-b-rehearsal",
  "credential_expiry": "2025-12-01T00:00:00Z",
  "emitted_at": "2025-11-15T12:00:00Z",
  "status": "aligned",
  "latency_ms": 83
}
```

This example mirrors the payload emitted after a successful Stage B handshake
where the gateway supplied the credential expiry timestamp. Custom diagnostic
fields (`status`, `latency_ms`) ride alongside the canonical telemetry without
violating the schema.
