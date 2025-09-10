# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Documented PyO3 and gRPC interface contracts in `NEOABZU/Reignition.md` and
  introduced a CI job that builds Rust crates and runs Python integration tests.
- Initialized NEOABZU Rust workspace with core lambda-calculus interpreter and Python bindings.
- Documented MCP connector compatibility matrix and integration roadmap; linked from project overview.
- Added OpenTelemetry API and OTLP exporter dependencies and setup guidance.
- Memory introspection API and dashboard panel for querying and purging chakra memories.
- Configurable tracer factory via ``TRACE_PROVIDER`` with examples for switching providers.
- Documented chakra-tagged signals, heartbeat propagation, and recovery flows
  across connector and operator guides; added tests for connector links.
- ``connectors.message_formatter`` wraps outbound messages with ``chakra``,
  ``version``, and ``recovery_url`` metadata and now checks ``RECOVERY_URL`` at
  call time.
- MCP gateway exposes context registration and model invocation via MCP; added `config/mcp.toml` and `docs/mcp_overview.md`.
- Mission builder with Ignite, Query Memory, and Dispatch Agent blocks plus server-side Save & Run routing through `agents/task_orchestrator`.
- Game dashboard onboarding wizard guides operators through creating and running their first mission with progress stored in `localStorage`.
- Unified Memory Bundle chapter clarifies `layer_init` and `query_memory` flow in `docs/ABZU_blueprint.md`.
- `docs/operator_onboarding.md` documents mission workflows with Mermaid diagrams and cross-links in `system_blueprint.md`.
- `datpars` placeholder package with stub interfaces and `docs/datpars_overview.md`.
- Documented Chakra Heartbeat Alignment for Nazarick agents with Mermaid mapping; cross-linked `chakra_metrics.md` and `ignition_blueprint.md`.
- Wrapped `agents.event_bus.emit_event` and memory layer queries with OpenTelemetry spans.
- Structured manual detailing chakra architecture, system components, memory bundle, and operator paths with Mermaid diagrams and doctrine cross-links.
- Blueprint manual capturing vision, chakra architecture, operator console routes, memory bundle initialization, and dynamic ignition.
- Added Nazarick stewardship section and integration diagrams linking Crown and RAZAR in core blueprints.
- Exposed `/healthz` and `/metrics` on the sidekick helper service.
- Documented Prometheus/Grafana dashboard setup in `docs/operations.md`.
- Query memory benchmark records throughput and latency with scheduled CI runs and a dedicated Makefile target.
- Clarified API vs MCP connector matrix and heartbeat `cycle_count` propagation across the system blueprint and blueprint spine.
- Documented heartbeat propagation, session management, and self-healing in
  `system_blueprint.md`, `blueprint_spine.md`, `avatar_pipeline.md`, and
  `operator_onboarding.md`; added cross-links from `GENESIS/README.md` and
  `README_OPERATOR.md` for quick reference.
- Added `scripts/validate_docs.py` and CI/pre-commit integration to enforce
  registry version alignment and cross-link validity.
- Track model endpoints and patches in `worlds.config_registry`; added
  `world export`/`world import` utilities and automatic registration of
  model endpoints.
- Expanded `bootstrap_world.py` to initialize memory layers, start Crown, and load agent profiles; exposed as `abzu-bootstrap-world`.
- `bootstrap_world.py` now logs completion after mandatory layers and agent profiles initialize.
- Enforced explicit health probes for RAZAR boot components and added boot
  sequence tests.
- Memory introspection API with query, purge, and snapshot endpoints plus web console memory panel.
- Documented operator-first principle and contributor guidance across core docs.

- `abzu-memory-bootstrap` script initializes memory layers in one step.
- Chakra watchdog emits `chakra_down` events with NAZARICK resuscitation.
- Chakra cycle defines per-chakra gear ratios and emits Great Spiral alignment events.
- Crown and RAZAR block routing on misalignment and trigger Nazarick remediation for silent chakras.
- Dashboard Avatar Room with quick avatar commands, mini missions, and per-agent selection.
- React-based game dashboard wrapping avatar stream and mission map actions.
- Detailed notes describe how the Chakra watchdog coordinates with the Resuscitator
  to restart failing layers and log recovery metrics.

- WebSocket `/operator/events` for command acknowledgements and progress with console subscription.
- Nazarick Web Console docs explain viewing agent interactions, NLQ log search, and live chat streams; added tests for paginated conversation logs.
- Arcade operator interface and UI service diagrams expand console theming guidance.

- Instrumented Crown, Bana and memory layers with Prometheus gauges, documented
  the copresence dashboard and added tests for metrics endpoints.

- Introduced chakra healing scripts and monitoring agents with logging and documentation.
- Gracefully handle missing memory layers in `aggregate_search` with tests and documentation.

- Emitted structured health events during RAZAR boot and introduced recovery daemon for automated restarts.
- Added `/operator/status` endpoint reporting component health, recent errors, and memory usage; bumped `operator_api` to 0.3.5.
- Runtime servant model registration: `servant_model_manager` now supports
  unregistering and reloading handlers, and `operator_api` exposes endpoints
  to add or remove servant models at runtime (v0.3.6).

- Added `environment.gpu.yml` and CPU/GPU Dockerfiles with pinned versions and documented hardware setup.
- Documented inner memory guide and diagrams in the documentation index and linked cross-references from the Blueprint Spine and System Blueprint.
- Added `docs/SOCIAL_INVESTOR_ONE_PAGER.md` summarizing the project for prospective social investors.
- Clarified heartbeat polling, event routing, and agent-specific recovery in core documentation.
- Added `docs/component_maturity.md` tracking documentation completeness, coverage, and open issues.
- Documented RAZAR self-healing overview with links to recovery playbook and Kimi integration.

- Documented onboarding triple-reading requirement and Nazarick Web Console access in `docs/operator_interface_GUIDE.md` and updated `docs/INDEX.md`.
- Web console streams avatar video, audio, and narrative text concurrently and `abzu operator-console --smoke-test` exercises a scripted session.
- Added `docs/operator_nazarick_bridge.md` detailing Vanna data flow, agent channels, and console usage; cross-referenced from onboarding and system docs.
- Expanded `docs/component_status.md` with detailed alpha/beta/stable criteria.
- Added `scripts/verify_component_maturity.py` and enforced its check in CI.
- Documented unified `layer_init` and `query_memory` flow with cross-layer diagrams in the Absolute Protocol, Blueprint Spine, and System Blueprint.

- Documented chakra-aligned test directories and 90% coverage rule in `docs/the_absolute_pytest.md`.

- Introduced IP-sensitive annotation registry and CI verification.
- Benchmark for concurrent memory queries with CSV output and performance report.

- Instrumented `agents.event_bus` with OpenTelemetry spans for trace collection.
- Exposed `/healthz` and `/metrics` across FastAPI service modules.
- Added operations guide instructions for viewing traces and metrics.
- Added `scripts/update_error_index.py` to record new log errors in `docs/error_registry.md`.
- Extended `scripts/capture_failing_tests.py` so pytest runs append results to `docs/testing/failure_inventory.md`.
- Configured CI to archive `htmlcov/` and log coverage metrics even when tests fail.

- Introduced `training/fine_tune_mistral.py` configuring mythological and project corpora.
- Extended `scripts/check_requirements.sh` to report missing Python modules.
- Published memory layer bus events and `query_memory` aggregator.
- Web console pulls conversation logs per agent with timeline view, NLQ log search, and operator onboarding prompts.
- Recorded mythology and project material datasets in `component_index.json`.
- Listed dataset licensing, version history, and evaluation metrics in `docs/bana_engine.md`.
- Implemented `bana/narrative_api.py` for narrative retrieval and streaming.
- Added `scripts/generate_protocol_task.py` to create protocol refinement tasks after six new entries and wired it into nightly CI.
- Added `scripts/check_memory_layers.py` gating Albedo on successful memory checks and recorded dataset paths in `component_index.json` and `docs/memory_architecture.md`.
- Added `scripts/init_memory_layers.py` for seeding memory stores and expanded
  memory architecture documentation with example queries.
- Added `scripts/require_connector_registry_update.py` and pre-commit hook to enforce connector registry updates; expanded connector index with planned narrative WebSocket entry.
- Persisted narrative engine stories and events to SQLite with optional Chroma search and exposed `narrative_api` in connector registry.
- Recorded sample biosignal datasets and tests covering ingestion, persistence, and retrieval.
- Enforced ≥90% coverage in CI workflows; pipelines fail when thresholds are not met.
- Added Chakracon polling notes and resource-state dialogue across Nazarick agent templates.
- Introduced Chakracon metric monitoring with `start_monitoring` hooks for multiple agents.
- Integrated Node Exporter, cAdvisor, and DCGM GPU exporter into monitoring stack, added network I/O watchdog metrics, and expanded Grafana dashboards.
- Added GPG-based release signing scripts and documentation for verifying build artifacts.
- Added `scan_todo_fixme` pre-commit hook to block `TODO`/`FIXME` markers and documented rule in The Absolute Protocol.
- Added GitHub Actions workflow `dependency-audit.yml` to run `pip-audit` and `npm audit`, failing on high-severity vulnerabilities and uploading reports.
- Cross-linked `docs/The_Absolute_Protocol.md`, `docs/project_mission_vision.md`, and `docs/nazarick_manifesto.md` for governance and ethics coherence.
- Added `scripts/require_module_docs.py` pre-commit hook ensuring new modules update `CHANGELOG.md` and `docs/component_index.md`.
- Connected `compose_multitrack_story` to `expressive_output` for synchronized audio and avatar frames.
- Updated web console to stream avatar video, play audio, and display prose in real time.
- Added sample outputs and troubleshooting guidance to `docs/narrative_system.md`.
- Added `docs/operator_quickstart.md` summarizing the triple-reading rule and consent logging.
- Introduced optional Opencode CLI handover in `razar.ai_invoker` with
  accompanying setup instructions in RAZAR docs.
- Enabled Opencode to delegate code generation to the Kimi-K2 servant model and documented setup in `docs/tools/kimi_integration.md`.

- Clarified test coverage expectations, error logging requirements, and added a milestone retrospective template in `docs/The_Absolute_Protocol.md`.

- Added `scripts/verify_doctrine_refs.py` pre-commit hook to ensure key doctrine docs stay indexed.

### Documentation Audit
- Expanded RAZAR agent guide with architecture diagram, requirements, deployment workflow, config schemas, cross-links, and example runs.
- Added step-by-step handover and patch application flow with `ai_invoker` → `code_repair` diagram and logging policy reference.
- Documented remote assistance workflow with flow diagram and integrated `code_repair.repair_module` into `ai_invoker.handover`.

- Mandated quarterly review of entries in `docs/KEY_DOCUMENTS.md` and added audit cadence table with `scripts/schedule_doc_audit.py`.
- Ensure components have descriptions and data-flow references.
- Linked chakra koan and version files from README and CONTRIBUTING.
- Added chakra status table in `docs/chakra_status.md` outlining capabilities,
  limitations and planned evolutions for each layer.
- Introduced `agents/nazarick/agent_registry.json` and updated service launcher for dynamic agent loading with channel status display.
- Linked release notes to `docs/chakra_versions.json` and `CHANGELOG.md`.
- Added recovery playbook documenting snapshot restoration steps.
- Mapped cortex, emotional, mental, spiritual and narrative memory stores in
  `docs/memory_architecture.md`.
- Documented Albedo layer personas and deployment logging.
- Expanded `docs/bana_engine.md` with architecture diagram, dependencies, dataset paths, failure scenarios, and version history; exposed `__version__` in Bana modules and synced `component_index.json`.
- Documented ignition flow from RAZAR through Bana to operator interface in
  `docs/ignition_flow.md`.
- Added INANNA core deployment notes and memory component entries in
  `component_index.json`.
- Documented RAZAR environment configuration schema in `docs/RAZAR_AGENT.md`.
- Added configuration schema diagrams, ignition example with log excerpts, and mission-brief archive notes to `docs/RAZAR_AGENT.md`; refreshed protocol compliance dashboard.
- Linked protocol compliance dashboard from RAZAR agent guide.
- Added `__version__` fields across modules and added version checks in `scripts/component_inventory.py`.
- Documented Nazarick agent triggers for Albedo state transitions and added
  state-to-channel table; refreshed `docs/INDEX.md`.


### Documentation

- Integrated ABZU Project Declaration into `docs/project_mission_vision.md`.
- Enforced Persona & Responsibilities and Component & Link sections in agent docs and updated contributor checklist.
- Updated Nazarick narrative system guide with mermaid pipeline diagram and removed obsolete image reference.
- Added Albedo layer state-machine diagram and deployment guide with sample configuration.
- Expanded Nazarick agent guide with deployment commands, channel mappings, and extensibility hooks.
- Documented Nazarick Web Console with mermaid layout diagram, dependencies, and connector links.
- Added "The Absolute pytest" guide for chakra-aligned tests and commit workflow.
- Introduced Pytest Protocol with >90% coverage, chakra-aligned directories, and component index documentation requirements.
- Expanded Crown agent overview with model loading sequence diagram and configuration table.
- Added Crown persona section with mission brief and chat transcript examples; referenced in The Absolute Protocol.
- Documented change justification rule and mandated four-part onboarding summaries; updated pull request template with connector/index checklist.
- Documented module coverage and example runs in RAZAR agent guide.
- RAZAR agent guide now requires `CROWN_WS_URL`, a running Crown server, and
  documents mission brief archive rotation.
- Added Change Justification subsection and PR template field with CI validation.
- Protocol v1.0.60 now requires `__version__` in every module, connector, and service and mandates documenting configuration schemas (e.g., `boot_config.json`, `primordials_config.yaml`, `operator_api.yaml`) with examples.
- Linked Operator Protocol from RAZAR agent guide and regenerated docs index.
- Mandated triple reading of `docs/blueprint_spine.md` in The Absolute Protocol.
- Introduced Connector Health Protocol requiring `scripts/health_check_connectors.py` to pass before merging.
- Clarified Change Justification rule with mandatory "I did X on Y to obtain Z, expecting behavior B" template.
- Documented Crown service wake sequence linking servant launch scripts and required `SERVANT_MODELS`/`NAZARICK_ENV` settings; cross-linked ignition flow and regenerated docs index.
- Referenced the task cycle script in The Absolute Protocol and refreshed the docs index.
- Extended component index schema to list Bana memory layers with ignition stages and updated ignition flow to show RAZAR triggering Bana after INANNA memory initialization; cross-linked Bana from RAZAR and memory architecture guides.
- Added `docs/chakra_metrics.md` mapping chakra layers to system metrics and thresholds; linked from `docs/INDEX.md`.

### Added

- Introduced protocol compliance dashboard and required dashboard updates each release cycle in The Absolute Protocol.
- Introduced lifecycle `status` and `adr` link requirements for `component_index.json` and provided `docs/adr/ADR_TEMPLATE.md`.
- Introduced co-creation and AI ethics frameworks with cross-links from README and The Absolute Protocol.
- Expanded connector registry schema with purpose and service fields and updated The Absolute Protocol accordingly.
- Added Code Harmony, API Contract, and Technology Registry protocols to The Absolute Protocol.
- Created connector index and documented registry rules in The Absolute Protocol.
- Added hyperlink requirement and illustrative component table to The Absolute Protocol.
- Added checklist reminder to update `CONNECTOR_INDEX.md` whenever connectors change.
- Required configuration files to include schema outlines and minimal examples, referencing `boot_config.json`, `razar_env.yaml`, and log formats.
- Added operator protocol for `/operator/command` and linked it under Subsystem Protocols in The Absolute Protocol.
- Mandated end-to-end run examples with logs covering normal operation and failure recovery in agent docs.
- Archived Crown handshake responses alongside mission briefs and
  auto-launched `GLM4V` when missing from advertised capabilities.
- Persisted Crown handshake acknowledgement and downtime under `handshake`
  in `logs/razar_state.json`.
- Logged handshake and model-launch events in `logs/razar_state.json` and mandated mission-brief logging for all handshakes in The Absolute Protocol.
- Archived GLM-4.1V launch events to `logs/mission_briefs/` and added tests
  for mission-brief archiving and GLM capability detection.
- Required a "Change justification" field in the pull request template and documented the statement format in The Absolute Protocol.
- Documented mission brief archive requirements and maintenance in The Absolute Protocol.
- Added Operator API and Open Web UI entries to `CONNECTOR_INDEX.md` and expanded protocol checklist for connector registry.
- Required onboarding summaries for all files listed in `onboarding_confirm.yml` and referenced the rule in The Absolute Protocol.
- Added Release Protocol to The Absolute Protocol covering changelog updates, git tagging, and release note cross-references.
- Clarified Release Management Protocol with semantic versioning rules and checklist references.
- Required logging of RAZAR ↔ Crown ↔ Operator exchanges in `logs/interaction_log.jsonl` and referenced rules in RAZAR and operator docs.
- Enforced Crown availability during boot and rotated mission brief archives under `logs/mission_briefs/`.
- Added Connector Guidelines section requiring version fields, endpoint documentation, and registry updates, enforced by a pre-commit check.
- Crown prompt orchestrator reviews test metrics and logs remediation suggestions to corpus memory.
- Extended Operator API and web console to support file uploads with metadata relayed to RAZAR via Crown, and documented `/operator/upload` authentication and rate limits.
- Added configurable audio and video track helpers with fallbacks to WebRTC server and connector.
- Pytest runs export coverage, session duration, and failure metrics via `prometheus_client` to `monitoring/pytest_metrics.prom`, and CI uploads the metrics artifact.
- Implemented AI handover workflow that delegates failures to remote agents,
  logging invocations and applied patch diffs.
- Added `scripts/validate_ignition.py` to validate the RAZAR → Crown → INANNA → Albedo → Nazarick → operator interface chain and log results to `logs/ignition_validation.json`.
- Added `scripts/health_check_connectors.py` to ping connectors and report readiness.
- AI handover now reads configurable agent endpoints and authentication
  tokens and retries components after automated patches are applied.
- Routed INANNA interactions through Bana, storing narratives in spiral memory
  and relaying quality metrics to the Primordials service.

### Quality

- Verified repository passes `ruff` and `black` checks.
- Enforced "No Placeholder" rule with `check-placeholders` pre-commit hook and
  documented remediation steps in agent guides.
- Hardened operator and Primordials connectors with additional error handling and version bumps.
- Added logging and fallback behaviour when the invocation engine is unavailable or fails.

### Vector Memory

- `snapshot` logs paths to `snapshots/manifest.json` for recovery tracking.
- Comments mention narrative hooks for cross-story references.

### Narrative Engine

- Expanded anonymized biosignal datasets with acquisition guidelines and
  ingestion script references.
- Extended tests to cover multiple samples and transformations.
- Introduced `sample_biosignals_gamma.csv` and documented ingestion schema with
  dedicated transformation tests.
- Stubbed `memory/narrative_engine.py` defining story event interfaces.
- Added `docs/nazarick_narrative_system.md` outlining architecture, dependencies,
  and biosignal event flow.
- Added `sample_biosignals_delta.csv` with schema and ingestion notes.
- Enhanced tests to validate numeric data and multi-file transformations.
- Replaced in-memory story log with SQLite-backed persistence and documented schema.

### Changed
- Optional memory layers load no-op fallbacks and report status "skipped" when dependencies are missing.
- Replaced Chat2DB ASCII pipeline with a Mermaid flowchart and linked storage layers.
- Operator onboarding steps now use Mermaid diagrams for voice selection and agent roster review instead of screenshots in `docs/operator_interface_GUIDE.md`.
- Assigned unique component IDs for avatar/audio generation modules and RAZAR health checks to avoid collisions, ensuring component lookups remain unambiguous.
- Bumped `crown_handshake` to 0.2.4 and `operator_api`/`webrtc_connector` to 0.3.3 and recorded versions in connector registry.
- Added mission brief and operator chat examples with connector checklist cross-links in Crown and operator docs.
- Removed unused `boot_sequence` placeholder from `orchestration_master.py`.
- Hardened Crown prompt orchestrator to target known exceptions and surface unexpected failures.
- Wrapped OpenTelemetry import in `memory.bundle` and defaulted to a no-op tracer when the package is absent.
- Moved OpenTelemetry dependencies to optional `tracing` extras.
- Boot orchestrator reruns health checks after AI-generated patches and stops
  after the configurable `--remote-attempts` limit, logging each handover.

### Chakra Versions

- Track semantic versions for each chakra layer in
  `docs/chakra_versions.json`.
- Record each chakra version bump in this changelog.
- Bumped `root` and `crown` chakras to `1.0.1`.
- Bumped `sacral` chakra to `1.0.1`.
- Bumped `heart` chakra to `1.0.1`.
- Bumped `solar_plexus` chakra to `1.1.0` after learning pipeline updates; see `docs/chakra_koan_system.md#solar`.
- Bumped `throat` chakra to `1.0.1` fixing prompt orchestration; see `docs/chakra_koan_system.md#throat`.
- Synced heart koan reference with the manifest.
- Bumped `third_eye` chakra to `1.0.1` for narrative memory integration.

### Insight Matrix

- Record versioned history of insight matrix updates in `insight_manifest.json`.

## [0.1.0] - 2025-08-23

### Added

- Initial release.
