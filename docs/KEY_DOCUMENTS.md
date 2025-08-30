# Key Documents

The files listed here are foundational and must never be deleted or renamed.
For each document below, contributors must store its SHA256 hash and a short
summary in `onboarding_confirm.yml` to prove the current version was reviewed.

## Protected Files

| Document | Description | Audit cadence |
| --- | --- | --- |
| [AGENTS.md](../AGENTS.md) | Repository-wide agent instructions | Quarterly |
| [The Absolute Protocol](The_Absolute_Protocol.md) | Core contribution rules | Quarterly |
| [System Blueprint](system_blueprint.md) | Architectural overview | Quarterly |
| [Component Index](component_index.md) | Inventory of modules and services | Quarterly |
| [Component Status](component_status.md) | Tracks component readiness | Quarterly |
| [Connector Index](connectors/CONNECTOR_INDEX.md) | Registry of connector IDs, purpose, versions, endpoints, auth methods, status, and links to docs and source code | Quarterly |
| [Security Model](security_model.md) | Threat modeling and protections | Quarterly |
| [Data Security and Compliance](data_security.md) | Compliance requirements | Quarterly |
| [Data Manifest](data_manifest.md) | Data sources and types | Quarterly |
| [Dependency Registry](dependency_registry.md) | Approved runtimes and library versions | Quarterly |
| [Logging Guidelines](logging_guidelines.md) | Structured logging requirements | Quarterly |
| [API Reference](api_reference.md) | API endpoints and schemas | Quarterly |
| [Operator Protocol](operator_protocol.md) | Operator interaction rules | Quarterly |
| [Test Planning Guide](onboarding/test_planning.md) | Filing "Test Plan" issues defining scope, chakra, and coverage goals | Quarterly |
| [RAZAR AI agents config](../config/razar_ai_agents.json) | Roster of handover agents and authentication settings | Quarterly |

These documents define repository-wide conventions and rules. Repository policy and pre-commit checks prevent their removal or renaming. When related components change, update the corresponding document in the same commit to keep information synchronized.

All Python modules must declare a `__version__` attribute. The `verify-versions`
pre-commit hook scans staged Python files and blocks commits when the attribute
is missing.

Contributors must also record a short summary for every protected file in
`onboarding_confirm.yml`. Each summary should note the document's purpose,
scope, and key rules.

## Onboarding Confirmation

After completing the [onboarding checklist](onboarding/README.md), create an
`onboarding_confirm.yml` file in the repository root that records, for each
required document, its hash and short summary:

```yaml
documents:
  AGENTS.md:
    sha256: <sha256>
    summary: "Guidelines for repository operations and agent conduct."
  docs/The_Absolute_Protocol.md:
    sha256: <sha256>
    summary: "Core contribution rules and governance."
```

The `confirm-reading` pre-commit hook verifies this file and blocks commits if
any listed document changes. The companion `verify-doc-hashes` hook recomputes
hashes for protected files and fails if `onboarding_confirm.yml` is out of date,
ensuring stored summaries stay aligned with their documents.
