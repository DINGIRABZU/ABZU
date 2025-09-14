# Chakrapulse Specification

Chakrapulse defines a lightweight heartbeat bus shared across ABZU crates and services.
It transports small **pulse** messages that advertise component health.

## Message Schema

| Field | Type | Description |
| --- | --- | --- |
| `source` | string | Identifier of the emitter. |
| `ok` | bool | `true` when the component reports healthy. |
| `timestamp` | u64 | Unix epoch seconds when the pulse was sent. |

## Heartbeat Cadence

Components emit a pulse every `5s` while operational. Consumers may
subscribe to the bus at any time; missed pulses are not replayed.

## Error Codes

| Code | Meaning |
| --- | --- |
| `0` | Delivered successfully. |
| `1` | No subscribers were available. |
| `2` | Internal bus failure. |

## Doctrine References

- [system_blueprint.md](system_blueprint.md)
