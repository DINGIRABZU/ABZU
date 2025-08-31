# Key Documents

The files listed here are foundational and must never be deleted or renamed.
For each document below, contributors must store its SHA256 hash and a
contributor summary detailing its purpose, scope, key rules, and one actionable
insight in `onboarding_confirm.yml` to prove the current version was reviewed.
This requirement is reinforced by The Absolute Protocol's
[Contributor Awareness Checklist](The_Absolute_Protocol.md#contributor-awareness-checklist).

## Protected Files

| Document | Description | Audit cadence |
| --- | --- | --- |
| [AGENTS.md](../AGENTS.md) | Repository-wide agent instructions | Quarterly |
| [The Absolute Protocol](The_Absolute_Protocol.md) | Core contribution rules | Quarterly |
| [System Blueprint](system_blueprint.md) | Architectural overview | Quarterly |
| [Project Mission & Vision](project_mission_vision.md) | Unified mission, vision, and purpose | Quarterly |
| [Component Index](component_index.md) | Inventory of modules and services | Quarterly |
| [Component Status](component_status.md) | Tracks component readiness | Quarterly |
| [Connector Index](connectors/CONNECTOR_INDEX.md) | Canonical registry of connector IDs, purpose, versions, endpoints, auth methods, status, and links to docs and source code. Update this index whenever connector details change. | Quarterly |
| [Connector Overview](connectors/README.md) | Maintenance rules and schema templates for connector implementations | Quarterly |
| [Connector Health Protocol](connector_health_protocol.md) | Requires `scripts/health_check_connectors.py` to pass before merging | Quarterly |
| [Security Model](security_model.md) | Threat modeling and protections | Quarterly |
| [Data Security and Compliance](data_security.md) | Compliance requirements | Quarterly |
| [Data Manifest](data_manifest.md) | Data sources and types | Quarterly |
| [Dependency Registry](dependency_registry.md) | Approved runtimes and library versions | Quarterly |
| [Logging Guidelines](logging_guidelines.md) | Structured logging requirements | Quarterly |
| [API Reference](api_reference.md) | API endpoints and schemas | Quarterly |
| [Operator Protocol](operator_protocol.md) | Operator interaction rules | Quarterly |
| [Test Planning Guide](onboarding/test_planning.md) | Filing "Test Plan" issues defining scope, chakra, and coverage goals | Quarterly |
| [Bana Engine](bana_engine.md) | Mistral 7B fine-tuning, event processing, and output paths | Quarterly |
| [Nazarick Narrative System](nazarick_narrative_system.md) | Biosignals-to-narrative event pipeline | Quarterly |
| [RAZAR AI agents config](../config/razar_ai_agents.json) | Roster of handover agents and authentication settings | Quarterly |
| [Environment check script](../scripts/check_env.py) | Verifies required packages and tools are installed | Each commit |

These documents define repository-wide conventions and rules. Repository policy
and pre-commit checks prevent their removal or renaming. When related components
change, update the corresponding document in the same commit to keep information
synchronized.

All Python modules must declare a `__version__` attribute. The `verify-versions`
pre-commit hook scans staged Python files and blocks commits when the attribute
is missing.

Contributors must also record a short summary for every protected file in
`onboarding_confirm.yml`. Each summary must note the document's purpose, scope,
key rules, and one actionable insight. At minimum, `onboarding_confirm.yml` must track the
current versions of `docs/system_blueprint.md`, `docs/connectors/CONNECTOR_INDEX.md`,
`docs/primordials_service.md`, and `docs/component_index.md` with hashed
summaries.

## Onboarding Confirmation

After completing the [onboarding checklist](onboarding/README.md), create an
`onboarding_confirm.yml` file in the repository root that records, for each
required document, its hash and four-part summary (purpose, scope, key rules,
and insight):

```yaml
documents:
  AGENTS.md:
    sha256: <sha256>
    summary:
      purpose: "Guidelines for repository operations and agent conduct."
      scope: "Entire repository"
      key_rules: "Run pre-commit and consult AGENTS.md before committing."
      insight: "Check AGENTS.md before committing changes."
  docs/The_Absolute_Protocol.md:
    sha256: <sha256>
    summary:
      purpose: "Core contribution rules and governance."
      scope: "All contributors"
      key_rules: "Record purpose, scope, key rules, and insight for key docs."
      insight: "Include an action summary in every pull request."
  docs/system_blueprint.md:
    sha256: <sha256>
    summary:
      purpose: "Architectural blueprint overview."
      scope: "System-wide architecture"
      key_rules: "Align component changes with blueprint structure."
      insight: "Align changes with blueprint structure."
  docs/connectors/CONNECTOR_INDEX.md:
    sha256: <sha256>
    summary:
      purpose: "Registry of connector details."
      scope: "All connectors"
      key_rules: "Update entries whenever connector information changes."
      insight: "Update entry whenever a connector changes."
  docs/primordials_service.md:
    sha256: <sha256>
    summary:
      purpose: "DeepSeek-V3 orchestration service guide."
      scope: "Primordials service"
      key_rules: "Follow documented orchestration endpoints."
      insight: "Reference when integrating Primordials."
  docs/component_index.md:
    sha256: <sha256>
    summary:
      purpose: "Inventory of modules and services."
      scope: "All components"
      key_rules: "Add or update entries for component changes."
      insight: "Add or update entries for component changes."
```

The `confirm-reading` pre-commit hook verifies this file and blocks commits if
any listed document changes. The companion `verify-doc-hashes` hook recomputes
hashes for protected files and fails if `onboarding_confirm.yml` is out of date,
ensuring stored summaries stay aligned with their documents.
