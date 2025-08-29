# The Absolute Protocol

**Version:** v1.0.15
**Last updated:** 2025-08-30

## How to Use This Protocol
This document consolidates ABZU's guiding rules. Review it before contributing to ensure you follow required workflows and standards.

## Contributor Awareness Checklist
Before opening a pull request, confirm each item:

- [ ] Key documents reviewed:
  - [AGENTS.md](../AGENTS.md)
  - [Documentation Protocol](documentation_protocol.md)
  - [System Blueprint](system_blueprint.md)
- [ ] `onboarding_confirm.yml` includes purpose, scope, key rules, and one actionable insight for each [key document](KEY_DOCUMENTS.md)
- [ ] Module `__version__` fields bumped for user-facing changes
- [ ] Connectors implement `start_call`, `close_peers`, and expose `__version__`
- [ ] If a connector is added or modified, update [CONNECTOR_INDEX.md](connectors/CONNECTOR_INDEX.md) with version and service details
- [ ] `docs/INDEX.md` regenerated if docs changed
- [ ] Confirm no binary files are introduced

## Protocol Hierarchy
The Absolute Protocol governs all other guides. Review subordinate protocols as needed:

- **The Absolute Protocol**
  - [AGENTS.md](../AGENTS.md) – repository-wide agent instructions.
  - [Documentation Protocol](documentation_protocol.md) – workflow for updating docs.
  - [Code Style Guide](../CODE_STYLE.md) – code formatting standards.
  - [Pull Request Template](../.github/pull_request_template.md) – required PR structure.
  - [Co-creation Framework](co_creation_framework.md) – feedback loops between developers and INANNA_AI.
  - [AI Ethics Framework](ai_ethics_framework.md) – transparency, fairness, and data-handling principles.
  - [Documentation Index](index.md) – high-level entry point.
  - [Generated Index](INDEX.md) – auto-generated list of all docs.
  - [Absolute Milestones](ABSOLUTE_MILESTONES.md) – summary of past and upcoming milestones.
  - [Issue & Feature Templates](../.github/ISSUE_TEMPLATE/) – templates for new issues and features.

## Consultation Order
When contributing, consult resources in this order:

1. **The Absolute Protocol** – canonical repository rules.
2. **[Contributor Handbook](CONTRIBUTOR_HANDBOOK.md)** – setup and workflows.
3. **[AGENTS.md](../AGENTS.md)** – directory-specific instructions.
4. **Feature or Issue Specs** – task-specific requirements.

| Protocol | Maintainer | Update Cadence |
| --- | --- | --- |
| The Absolute Protocol | Core Maintainers | Monthly |
| Contributor Handbook | Documentation Team | Quarterly |
| AGENTS.md | Repository Maintainers | As needed |
| Feature/Issue Specs | Feature Owners | Per release |

## Documentation Standards

### Agent Documentation Checklist
Each agent document must cover:
- Vision
- Module Overview
- Functional Workflows
- Architecture diagram
- Requirements
- Deployment workflow
- Configuration schemas
- Version history
- Cross-links
- Hyperlinks to relevant source files and companion documents
- At least one end-to-end run with sample logs or outputs covering normal operation and one failure/recovery case where applicable

Include hyperlinks to implementation files and related guides. Use a table pattern
similar to the RAZAR component links to summarize relationships:

| Source Module | Companion Docs |
| --- | --- |
| [agents/example_agent.py](../agents/example_agent.py) | [example_agent.md](example_agent.md), [system_blueprint.md](system_blueprint.md) |

### Configuration File Documentation

Any new configuration file must be accompanied by documentation that outlines its schema and includes a minimal working example. Review existing patterns such as [boot_config.json](RAZAR_AGENT.md#boot_configjson), [razar_env.yaml](RAZAR_AGENT.md#razar_envyaml), and the log formats in the [logging guidelines](logging_guidelines.md).

### Module Versioning

Every source module must expose a `__version__` field (or equivalent) and increment it for any user‑facing change. Run `scripts/component_inventory.py` to confirm module versions remain synchronized.

### Connector Guidelines

Connectors bridge the language engine to external communication layers. Follow the architecture in [Video Engine and Connector Design](design.md) when implementing new back ends. Each connector must:

- implement `start_call(path: str) -> None` to initiate a stream
- provide `close_peers() -> Awaitable[None]` to release resources
- expose a `__version__` field and bump it on interface changes
- cross-link implementation modules such as [`connectors/webrtc_connector.py`](../connectors/webrtc_connector.py) and the package [`connectors`](../connectors/__init__.py)

### Connector Registry

Track all connectors in [`docs/connectors/CONNECTOR_INDEX.md`](connectors/CONNECTOR_INDEX.md). Each entry must list the connector name, `__version__`, endpoint, authentication method, status, and links to documentation and source code. See [Connector Overview](connectors/README.md) for shared design patterns. Update this registry whenever a connector is added, removed, or its interface changes.

### Code Harmony Protocol

- Use consistent naming conventions across files, classes, and functions.
- Maintain clear module boundaries to prevent tight coupling.
- Every module must declare a `__version__` field for traceability.

### API Contract Protocol

- Document request and response schemas for all public interfaces.
- Version API contracts and avoid breaking changes without incrementing.
- Maintain a changelog entry for each contract update.

### Technology Registry Protocol

- Record approved runtimes, frameworks, and library versions.
- Update the registry when dependencies are added, upgraded, or deprecated.

## Maintenance
Whenever this file changes:
1. Regenerate `docs/INDEX.md` with `python tools/doc_indexer.py`.
2. Run `pre-commit run --files docs/The_Absolute_Protocol.md docs/INDEX.md`.

## Protocol Change Process
Updates to this protocol follow a lightweight governance model:

1. **Proposal** – Open an issue describing the rationale and desired changes.
2. **Implementation** – Submit a pull request referencing the issue and label it `Protocol Update` to surface review.
3. **Review** – Core maintainers discuss the proposal, request revisions, and approve when consensus is reached.
4. **Versioning** – Upon merge, update the version and last‑updated date at the top of this file and document the change in the repository changelog.

### Change Justification
Every pull request must include a statement in the **Change justification** section formatted as:

"I did X on Y to obtain Z, expecting behavior B."

This justification clarifies the action taken, the context, the observed result, and the intended outcome. The dedicated field in the pull request template makes this requirement explicit so reviewers can verify the rationale.

This process ensures the protocol evolves transparently and stays in sync with repository practices.

