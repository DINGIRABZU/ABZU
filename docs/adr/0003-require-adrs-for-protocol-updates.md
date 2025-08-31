# ADR 0003: Require ADRs for Absolute Protocol Updates

- **Status:** Accepted
- **Date:** 2025-08-31

## Context
`docs/The_Absolute_Protocol.md` defines core contribution rules. Changes to this protocol impact all collaborators and must be justified and discoverable.

## Decision
Any modification to `docs/The_Absolute_Protocol.md` must include a corresponding ADR in `docs/adr/` that outlines the motivation for the change and alternatives considered. The ADR must be referenced in `docs/INDEX.md` and in `component_index.json` for affected components.

## Alternatives
- Allow direct edits to the protocol without ADRs, relying solely on commit messages.
- Track discussion through issues without formal ADR documentation.

## Consequences
- Provides a historical record of protocol decisions.
- Adds documentation overhead but improves transparency and traceability.

## References
- [The Absolute Protocol](../The_Absolute_Protocol.md)
