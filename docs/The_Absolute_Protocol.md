# The Absolute Protocol

**Version:** v1.0.34
**Last updated:** 2025-09-12

## How to Use This Protocol
This document consolidates ABZU's guiding rules. Review it before contributing to ensure you follow required workflows and standards. Every module must declare a `__version__` attribute and keep it synchronized with [`component_index.json`](../component_index.json).

## Contributor Awareness Checklist
Before opening a pull request, confirm each item:

- [ ] Key documents reviewed:
  - [AGENTS.md](../AGENTS.md)
  - [Documentation Protocol](documentation_protocol.md)
  - [System Blueprint](system_blueprint.md)
- [ ] All modules expose `__version__`; bump fields for user-facing changes and sync with `component_index.json`
- [ ] Component index entry added/updated in [component_index.md](component_index.md)
- [ ] Connector registry updated:
  - implementations expose `__version__`, implement `start_call`, and `close_peers`
  - [CONNECTOR_INDEX.md](connectors/CONNECTOR_INDEX.md) entry updated
- [ ] API changes documented in [api_reference.md](api_reference.md) and connector docs
- [ ] Pull request includes change justification in the required format
- [ ] `onboarding_confirm.yml` logs purpose, scope, key rules, and one actionable insight for every file it tracks, per [KEY_DOCUMENTS.md](KEY_DOCUMENTS.md)
- [ ] `scripts/verify_doc_summaries.py` confirms `onboarding_confirm.yml` hashes match current files
- [ ] `scripts/verify_versions.py` confirms module versions match `component_index.json`
- [ ] `docs/INDEX.md` regenerated if docs changed
- [ ] `component_maturity.md` scoreboard updated
- [ ] New operator channels documented in [Operator Protocol](operator_protocol.md)
- [ ] Confirm no binary files are introduced
- [ ] All diagrams are authored in Mermaid; binary image files (PNG, JPG, etc.) are forbidden
- [ ] Handshake-triggered model launches documented in agent guides and state logs

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

## Testing Requirements

- Run `pytest tests/narrative_engine/test_biosignal_pipeline.py` to validate
  biosignal ingestion and transformation.

## Test Coverage Protocol

Code coverage must remain **at or above 85%**. Generate and report coverage using:

```bash
pytest --cov
coverage report
coverage-badge -o coverage.svg
```

The `coverage.svg` badge reflects current totals and should be referenced in
status documents.

## Documentation Standards

### Agent Documentation Checklist
Each agent document must cover:
- Vision
- Module Overview
- Functional Workflows
- Architecture diagram
- Requirements
- Deployment workflow with environment setup, launch sequence, rollback strategy, and cross-links to subsystem-specific deployment sections (e.g., RAZAR Agent, Albedo Layer, Nazarick agents)
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

### Diagram Requirements

All diagrams must include a brief textual description and be expressed as Mermaid code blocks. Binary image formats (PNG, JPG, etc.) are prohibited.

#### Mermaid Diagram Workflow

- Write narrative explanation first.
- Represent visuals with Mermaid code blocks.
- Run `pre-commit run --files <changed_docs>` to trigger the `block-binaries` hook.
- Convert existing binary diagrams to Mermaid before committing.

### Configuration File Documentation

Any new configuration file must be accompanied by documentation that outlines its schema and includes a minimal working example. Review existing patterns such as [boot_config.json](RAZAR_AGENT.md#boot_configjson), [razar_env.yaml](RAZAR_AGENT.md#razar_envyaml), and the log formats in the [logging guidelines](logging_guidelines.md).

### Module Versioning

Every source module must expose a `__version__` field (or equivalent), increment it for any user‑facing change, and ensure the value matches the corresponding entry in `component_index.json`. Run `scripts/verify_versions.py` to confirm module versions remain synchronized.

### Connector Guidelines

Connectors bridge the language engine to external communication layers. Follow the architecture in [Video Engine and Connector Design](design.md) when implementing new back ends. Each connector must:

- implement `start_call(path: str) -> None` to initiate a stream
- provide `close_peers() -> Awaitable[None]` to release resources
- expose a `__version__` field and bump it on interface changes
- cross-link implementation modules such as [`connectors/webrtc_connector.py`](../connectors/webrtc_connector.py) and the package [`connectors`](../connectors/__init__.py)

### Connector Registry

Track all connectors in [`docs/connectors/CONNECTOR_INDEX.md`](connectors/CONNECTOR_INDEX.md). Each entry must list the connector name, `__version__`, endpoints, protocols, status, and links to documentation and source code. See [Connector Overview](connectors/README.md) for shared design patterns and maintenance rules. Update this registry whenever a connector is added, removed, or its interface changes.

#### Crown Handshake

Mission briefs exchanged during the Crown Handshake are archived at
`logs/mission_briefs/<timestamp>.json`. Keep this directory maintained to
preserve handshake history for auditing.

## Subsystem Protocols

- [Operator Protocol](operator_protocol.md) – outlines `/operator/command`, role checks, and Crown's relay to RAZAR.
- [Co-creation Escalation](co_creation_escalation.md) – defines when RAZAR seeks Crown or operator help and the logging for each tier.

### Code Harmony Protocol

- Use consistent naming conventions across files, classes, and functions.
- Maintain clear module boundaries to prevent tight coupling.
- Every module must declare a `__version__` field for traceability.

#### No placeholder comments

`TODO` and `FIXME` markers are prohibited in committed code. Open an issue or
implement the required change instead of leaving placeholders.

### API Contract Protocol

- Document request and response schemas for all public interfaces.
- Version API contracts and avoid breaking changes without incrementing.
- Maintain a changelog entry for each contract update.

### Technology Registry Protocol

- Maintain the [Dependency Registry](dependency_registry.md) of approved runtimes, frameworks, and library minimum versions.
- Update the registry when dependencies are added, upgraded, or deprecated, and validate changes with `pre-commit run --files docs/dependency_registry.md docs/INDEX.md`.

## Maintenance Checklist
- [ ] Regenerate `docs/INDEX.md` with `python tools/doc_indexer.py`.
- [ ] Run `pre-commit run --files docs/The_Absolute_Protocol.md docs/dependency_registry.md docs/INDEX.md onboarding_confirm.yml`.
- [ ] Run `scripts/verify_doc_summaries.py` to confirm `onboarding_confirm.yml` hashes.
- [ ] Ensure connectors appear in [CONNECTOR_INDEX.md](connectors/CONNECTOR_INDEX.md).

## Protocol Change Process
Updates to this protocol follow a lightweight governance model:

1. **Proposal** – Open an issue describing the rationale and desired changes.
2. **Implementation** – Submit a pull request referencing the issue and label it `Protocol Update` to surface review.
3. **Review** – Core maintainers discuss the proposal, request revisions, and approve when consensus is reached.
4. **Versioning** – Upon merge, update the version and last‑updated date at the top of this file and document the change in the repository changelog.

### Change Justification
Every pull request must include a statement in the **Action summary** section formatted as:

"I did X on Y to obtain Z, expecting behavior B."

This justification clarifies the action taken, the context, the observed result, and the intended outcome. The pull request template enforces this via a mandatory **Action summary** field in [`.github/pull_request_template.md`](../.github/pull_request_template.md) so reviewers can verify the rationale.

This process ensures the protocol evolves transparently and stays in sync with repository practices.

