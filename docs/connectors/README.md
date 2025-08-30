# Connector Overview

Canonical guidelines for modules that bridge Spiral OS to external services.
The live registry of available connectors lives in
[`CONNECTOR_INDEX.md`](CONNECTOR_INDEX.md).

## Vision

Provide lightweight bridges between Spiral OS and external services while
maintaining clear versioning and protocols.

## Architecture Diagram

```mermaid
flowchart LR
    SpiralOS --> Connector --> Service[External Service]
```

## Maintenance Rules

To keep integration layers discoverable and reliable:

- Expose a `__version__` field for traceability.
- Provide one or more callable endpoints or interfaces.
- Document authentication and network protocols used.
- Update the entry in [CONNECTOR_INDEX.md](CONNECTOR_INDEX.md) whenever
  purpose, versions, endpoints, or protocols change.
- Increment `__version__` for any backward-incompatible change.
- Keep modules lightweight with clear dependencies and minimal side effects.
- Supply or update tests and docs alongside connector changes.

## Requirements

- Python 3.10+
- Network libraries as needed by each connector

## Deployment

Install required dependencies and import the connector module in your service
or agent.

## Configuration Schemas

Each connector documents its authentication parameters. See
[`CONNECTOR_INDEX.md`](CONNECTOR_INDEX.md) for field descriptions.

## Version History

- v0.1.0 – initial connector guidelines

## Schemas

### `/operator/command`

```json
{
  "operator": "string",
  "agent": "string",
  "command": "string"
}
```

### `/operator/upload`

`multipart/form-data` fields:

| field | type | required | description |
| --- | --- | --- | --- |
| `operator` | string | yes | identity issuing the upload |
| `metadata` | JSON string | no | context forwarded to RAZAR |
| `files` | file[] | yes | one or more files to store |

These conventions keep integration layers consistent, discoverable, and easy to
maintain.
