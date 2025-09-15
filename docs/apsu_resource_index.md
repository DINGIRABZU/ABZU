# APSU Resource Index

Catalog of APSU and Neo-APSU resources across the repository. Each entry notes the file location, its role, and how it interacts with the RAZAR mission flow and Crown or assistant agents.

| Resource | Role | RAZAR/Crown Context |
| --- | --- | --- |
| [connectors/neo_apsu_connector_template.py](../connectors/neo_apsu_connector_template.py) | Template for building Neo-APSU connectors with MCP handshake and heartbeat telemetry. | Connectors feed RAZAR signals and route them to Crown and assistant agents. |
| [docs/mcp_overview.md](mcp_overview.md) | Gateway overview with steps for building Neo-APSU connectors. | Ensures connectors align with RAZAR missions and Crown routing. |
| [docs/onboarding/README.md](onboarding/README.md) | Contributor checklist for APSU and Neo-APSU docs. | Introduces Crown router, RAG orchestrator, and assistant agents. |
| [docs/onboarding/wizard.py](onboarding/wizard.py) | Script prompting Neo-APSU doc confirmations. | Validates contributor readiness for RAZAR and Crown components. |
| [docs/documentation_protocol.md](documentation_protocol.md) | Documentation rules including APSU sequence placement. | Links updates to blueprint diagrams of RAZAR and Crown flows. |
| [docs/migration_protocol.md](migration_protocol.md) | Guidelines for Python→Rust migrations. | Requires linking to APSU sequence diagrams for RAZAR and Crown. |
| [docs/migration_playbooks/crown.md](migration_playbooks/crown.md) | Playbook for Crown migration. | Verifies APSU sequence alignment with RAZAR control. |
| [docs/migration_playbooks/razar.md](migration_playbooks/razar.md) | Playbook for RAZAR migration. | Documents APSU placement within the RAZAR mission flow. |
| [docs/The_Absolute_Protocol.md](The_Absolute_Protocol.md) | Core contribution rules. | Rust migration rules reference APSU sequence and Crown handoff. |
| [docs/core_usage.md](core_usage.md) | Demonstrates importing Neo-APSU modules. | Shows how components interface with Crown and assistant agents. |
| [docs/component_index.md](component_index.md) | Index of repository components. | Lists Neo-APSU connector template used by RAZAR routing. |
| [AGENTS.md](../AGENTS.md) | Repository-wide instructions. | Notes procedures for Neo-APSU contributions affecting RAZAR and Crown. |
| [CHANGELOG.md](../CHANGELOG.md) | Release history. | Records updates to Neo-APSU connectors in the mission stack. |
| [NEOABZU/docs/index.md](../NEOABZU/docs/index.md) | NEOABZU documentation index. | References APSU architecture supporting RAZAR modules. |
| [onboarding_confirm.yml](../onboarding_confirm.yml) | Registry of doc confirmations. | Tracks acknowledgment of Neo-APSU materials tied to RAZAR agents. |

Backlinks: [System Blueprint](system_blueprint.md)
