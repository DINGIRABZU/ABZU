# The Absolute Protocol

**Version:** v1.0.47
**Last updated:** 2025-08-30

## How to Use This Protocol
This document consolidates ABZU's guiding rules. Review it before contributing to ensure you follow required workflows and standards. Every module must declare a `__version__` attribute.

## Contributor Awareness Checklist
Before opening a pull request, confirm each item:

- [ ] Key documents reviewed:
  - [AGENTS.md](../AGENTS.md)
  - [Documentation Protocol](documentation_protocol.md)
  - [System Blueprint](system_blueprint.md)
  - [Key Documents](KEY_DOCUMENTS.md) – verify all entries reviewed within the last quarter
- [ ] All modules expose `__version__`; the `verify-versions` pre-commit hook enforces this and fields must be bumped for user-facing changes
- [ ] Component index entry added/updated in [component_index.md](component_index.md)
- [ ] `ignition_stage` set for each component in `component_index.json` and reflected in [Ignition Map](ignition_map.md); see [Ignition](Ignition.md) for boot priorities
- [ ] Each `component_index.json` entry declares a lifecycle `status` (`active`, `deprecated`, or `experimental`) and links to an `adr` describing major changes
- [ ] Connector registry updated:
  - implementations expose `__version__`, implement `start_call`, and `close_peers`
  - [CONNECTOR_INDEX.md](connectors/CONNECTOR_INDEX.md) entry updated
- [ ] If a connector is added or modified, update [docs/connectors/CONNECTOR_INDEX.md](connectors/CONNECTOR_INDEX.md) with version, purpose, service, status, and links
- [ ] API changes documented in [api_reference.md](api_reference.md) and connector docs
- [ ] Release notes updated in `CHANGELOG.md` and relevant component changelog(s)
- [ ] Pull request includes change justification in the required format
- [ ] `onboarding_confirm.yml` logs purpose, scope, key rules, and one actionable insight for every file it tracks, per [KEY_DOCUMENTS.md](KEY_DOCUMENTS.md)
- [ ] `scripts/verify_doc_summaries.py` confirms `onboarding_confirm.yml` hashes match current files
- [ ] `docs/INDEX.md` regenerated if docs changed
- [ ] `DASHBOARD.md` metrics updated for each release cycle
- [ ] `component_maturity.md` scoreboard updated
- [ ] New operator channels documented in [Operator Protocol](operator_protocol.md)
- [ ] Confirm no binary files are introduced
- [ ] All diagrams are authored in Mermaid; binary image files (PNG, JPG, etc.) are forbidden
- [ ] Handshake-triggered model launches documented in agent guides and state logs
- [ ] `crown_handshake` results logged in state files and mission briefs

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

## Release Management Protocol

- Add an entry to the root `CHANGELOG.md` for every user-facing change.
- Mirror those entries in component changelogs such as `CHANGELOG_vector_memory.md` when a specific subsystem is affected.
- Version numbers follow [Semantic Versioning](https://semver.org/):
  - **MAJOR** increments introduce incompatible API changes.
  - **MINOR** increments add functionality in a backward‑compatible manner.
  - **PATCH** increments deliver backward‑compatible bug fixes.
- Within a major version, minor and patch releases guarantee backward compatibility.

## Testing Requirements

- Run `pytest tests/narrative_engine/test_biosignal_pipeline.py` to validate
  biosignal ingestion and transformation.
- Execute `pytest` (or an equivalent test suite) for all modules you modify and
  report the resulting coverage.

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

Every source module must expose a `__version__` field (or equivalent) and increment it for any user‑facing change. Run `scripts/component_inventory.py` to confirm module versions remain synchronized.
The `verify-versions` pre-commit hook scans staged Python files and fails if this attribute is missing.

### Connector Guidelines

Connectors bridge the language engine to external communication layers. Follow the architecture in [Video Engine and Connector Design](design.md) when implementing new back ends. Each connector must:

- implement `start_call(path: str) -> None` to initiate a stream
- provide `close_peers() -> Awaitable[None]` to release resources
- expose a `__version__` field and bump it on interface changes
- cross-link implementation modules such as [`connectors/webrtc_connector.py`](../connectors/webrtc_connector.py) and the package [`connectors`](../connectors/__init__.py)

### Connector Registry

Track all connectors in [`docs/connectors/CONNECTOR_INDEX.md`](connectors/CONNECTOR_INDEX.md). Each entry must list the connector name, `__version__`, purpose, service, endpoints, protocols, status, and links to documentation and source code. See [Connector Overview](connectors/README.md) for shared design patterns and maintenance rules. Update this registry whenever a connector is added, removed, or its interface changes.

#### Crown Handshake

Mission briefs exchanged during the Crown Handshake are archived at
`logs/mission_briefs/<timestamp>.json`. Keep this directory maintained to
preserve handshake history for auditing.

## Subsystem Protocols

- [Operator Protocol](operator_protocol.md) – outlines `/operator/command`, role checks, and Crown's relay to RAZAR.
- [Co-creation Escalation](co_creation_escalation.md) – defines when RAZAR seeks Crown or operator help and the logging for each tier.
- [Logging & Observability Protocol](#logging--observability-protocol) – structured logging and metrics requirements.

### RAZAR ↔ Crown ↔ Operator Interaction Logging

All exchanges between RAZAR, Crown, and Operator must append JSON lines to
`logs/interaction_log.jsonl` capturing:

- timestamp
- initiator
- action or request
- response summary

### Logging & Observability Protocol

- Follow the [logging guidelines](logging_guidelines.md) for JSON log formats and approved log levels.
- Consult the [Monitoring Guide](monitoring.md) for telemetry collection and Prometheus scraping.
- Module documentation must describe emitted log formats, enumerated log levels, and any Prometheus metrics exposed.

### Security Protocol

- Handle credentials according to the [Security & Secrets Protocol](#security--secrets-protocol); store sensitive values only in `secrets.env`.
- Run automated scanners such as `pip-audit`, `bandit`, and container image checks in CI to detect vulnerabilities and leaked secrets.
- Rotate all service credentials at least quarterly and immediately after a suspected exposure; document rotations in change logs.

### Security & Secrets Protocol

- Keep secrets in `secrets.env` (based on `secrets.env.template`) and never commit confidential keys.
- Enforce least-privilege access controls and audit sensitive operations.
- Consult [Security Model](security_model.md) and [Data Security and Compliance](data_security.md) for threat modeling and compliance guidance.

### Code Harmony Protocol

- Use consistent naming conventions across files, classes, and functions.
- Maintain clear module boundaries to prevent tight coupling.
- Every module must declare a `__version__` field for traceability.

#### No placeholder comments

`TODO` and `FIXME` markers are prohibited in committed code. Open an issue or
implement the required change instead of leaving placeholders. The
`check-placeholders` pre-commit hook runs `scripts/check_placeholders.py` to
block commits that include these markers.

### API Contract Protocol

- Document request and response schemas for all public interfaces.
- Version API contracts and avoid breaking changes without incrementing.
- Maintain a changelog entry for each contract update.

### API Schema Protocol

All endpoints must publish machine-validated schemas:

- **HTTP endpoints** require OpenAPI or JSON Schema definitions. Commit the
  generated spec to `docs/schemas/` and keep it synchronized with the running
  application.
- **WebSocket channels** must document message formats using JSON Schema files
  stored in `docs/schemas/`.
- Continuous integration must verify that committed schemas match the server's
  live specification.

### Technology Registry Protocol

- Maintain the [Dependency Registry](dependency_registry.md) of approved runtimes, frameworks, and library minimum versions.
- Update the registry when dependencies are added, upgraded, or deprecated, and validate changes with `pre-commit run --files docs/dependency_registry.md docs/INDEX.md`.

## Release Protocol

- Update [`CHANGELOG.md`](../CHANGELOG.md) or the relevant component changelog whenever a version number changes.
- Create an annotated git tag for each release (e.g., `git tag -a vX.Y.Z -m "Release vX.Y.Z"` and `git push --tags`).
- Cross-reference release details in [release_notes.md](release_notes.md) to capture highlights and migration notes.

## Maintenance Checklist
- [ ] Regenerate `docs/INDEX.md` with `python tools/doc_indexer.py`.
- [ ] Audit documents in KEY_DOCUMENTS.md quarterly and log overdue items with `scripts/schedule_doc_audit.py`.
- [ ] Run `pre-commit run --files docs/The_Absolute_Protocol.md docs/dependency_registry.md docs/INDEX.md onboarding_confirm.yml`.
- [ ] Run component tests with `pytest --cov` and attach the coverage badge or report to the PR.
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

