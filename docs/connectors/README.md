# Connector Overview

Connectors bridge Spiral OS to external communication services. Each connector follows these patterns:

- Exposes a `__version__` field for traceability.
- Provides a callable endpoint or interface such as `start_call` and `close_peers`.
- Documents authentication requirements for its target service.
- Registers its service details in [CONNECTOR_INDEX.md](CONNECTOR_INDEX.md).

These conventions keep integration layers consistent and discoverable.
