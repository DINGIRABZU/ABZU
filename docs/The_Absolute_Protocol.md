# The Absolute Protocol

**Version:** v1.0.0  
**Last updated:** 2025-08-28

## How to Use This Protocol
This document consolidates ABZU's guiding rules. Review it before contributing to ensure you follow required workflows and standards.

## Core Protocol References
- [AGENTS.md](../AGENTS.md) – repository-wide agent instructions.
- [Documentation Protocol](documentation_protocol.md) – workflow for updating docs.
- [Code Style Guide](../CODE_STYLE.md) – code formatting standards.
- [Pull Request Template](../.github/pull_request_template.md) – required PR structure.
- [Documentation Index](index.md) – high-level entry point.
- [Generated Index](INDEX.md) – auto-generated list of all docs.
- [Issue Templates](../.github/ISSUE_TEMPLATE/) – templates for new issues.

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

## Maintenance
Whenever this file changes:
1. Regenerate documentation indices: `python tools/doc_indexer.py`.
2. Run `pre-commit run --files docs/The_Absolute_Protocol.md docs/INDEX.md`.

