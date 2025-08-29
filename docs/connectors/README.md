# Connector Overview

Connectors bridge Spiral OS to external communication services. Each connector follows these patterns and maintenance rules:

**Common Patterns**

- Exposes a `__version__` field for traceability.
- Provides one or more callable endpoints or interfaces.
- Documents authentication and network protocols used.

**Maintenance Rules**

- Update the entry in [CONNECTOR_INDEX.md](CONNECTOR_INDEX.md) whenever versions, endpoints, or protocols change.
- Increment `__version__` for any backward-incompatible changes.
- Keep modules lightweight with clear dependencies and minimal side effects.
- Supply or update tests and docs alongside connector changes.

These conventions keep integration layers consistent, discoverable, and easy to maintain.
