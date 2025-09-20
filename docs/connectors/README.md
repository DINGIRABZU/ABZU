# Connector Overview

Guidelines for modules that bridge Spiral OS to external services. The live registry of available connectors lives in [CONNECTOR_INDEX.md](CONNECTOR_INDEX.md).

This overview is referenced by [Key Documents](../KEY_DOCUMENTS.md) and [The Absolute Protocol](../The_Absolute_Protocol.md).

## Maintenance Rules

To keep integration layers discoverable and reliable:

- Expose a `__version__` field for traceability.
- Provide one or more callable endpoints or interfaces.
- Document authentication and network protocols used.
- Update the entry in [CONNECTOR_INDEX.md](CONNECTOR_INDEX.md) whenever purpose, versions, endpoints, or protocols change.
- Increment `__version__` for any backward-incompatible change.
- Keep modules lightweight with clear dependencies and minimal side effects.
- Supply or update tests and docs alongside connector changes.
- Publish JSON or YAML schemas for request and response payloads in `schemas/` and link them from [CONNECTOR_INDEX.md](CONNECTOR_INDEX.md).

## Doctrine Compliance Checklist

Before deploying a Neo-APSU connector, satisfy the doctrine requirements codified in [The Absolute Protocol](../The_Absolute_Protocol.md#connector-registry-protocol):

1. **Registry entry present.** Register the connector in `component_index.json` and [CONNECTOR_INDEX.md](CONNECTOR_INDEX.md) with matching `id`, `path`, and `__version__` values so inventory tooling recognises the component.
2. **Schema alignment.** Maintain the linked schema under `schemas/`, ensuring Stage B heartbeats require `chakra`, `cycle_count`, `context`, `credential_expiry`, and `emitted_at`, with `context` locked to `stage-b-rehearsal`.
3. **Credential freshness.** Populate the MCP capability payload with up-to-date rotation metadata (`rotation.last_rotated`, `rotation_window`, `supports_hot_swap`) and document overrides in [mcp_capability_payload.md](mcp_capability_payload.md) so operators can audit credential health.

## Schema Conventions

Connector entries share common fields:

- **purpose** – short description of the connector's role.
- **version** – semantic identifier of the connector release.
- **endpoints** – network paths or methods exposed.
- **linked_agents** – agents or services that interact through the connector.
- **status** – lifecycle indicator (`experimental`, `active`, `deprecated`).
- For operator interfaces, document supported chat, file, image, audio, and video flows.
- **schema** – path to a JSON or YAML schema describing request and response bodies.

### Connector Entry Template

```json
{
"id": "example_connector",
"purpose": "short description",
"version": "1.0.0",
"endpoints": ["POST /example"],
  "linked_agents": ["example_agent"],
  "status": "experimental",
  "schema": "schemas/example_connector.schema.json"
}
```

### Operator API Examples

#### `/operator/command`
```json
{
  "operator": "string",
  "agent": "string",
  "command": "string"
}
```

#### `/operator/upload`
`multipart/form-data` fields:

| field | type | required | description |
| --- | --- | --- | --- |
| `operator` | string | yes | identity issuing the upload |
| `metadata` | JSON string | no | context forwarded to RAZAR |
| `files` | file[] | yes | one or more files to store |

These conventions keep integration layers consistent, discoverable, and easy to maintain.

## Version History

- v0.3.0 – added connector entry template and clarified maintenance rules
- v0.2.0 – condensed overview of maintenance rules and schemas
- v0.1.0 – initial connector guidelines
