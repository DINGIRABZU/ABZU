<!--
Prefix the PR title with a category such as `Feature:`, `Fix:`, or `Chore:` (e.g.,
`Feature: Voice Cloning V2`). Link any relevant documentation or specifications
below.
-->

## Summary
<!-- Required: provide a concise summary of the change. -->

## Linked issue/feature spec
<!-- Required: link to the relevant issue, documentation, or feature spec. -->

## Action summary (I did X on Y to obtain Z, expecting behavior B)
<!-- Required: follow the format above exactly for your change. -->
<!-- If a connector was added or modified, update [CONNECTOR_INDEX.md](../docs/connectors/CONNECTOR_INDEX.md) with purpose, version, endpoints, auth method, status, and code/documentation links, as required by [The Absolute Protocol](../docs/The_Absolute_Protocol.md). -->

## Task Registry
<!-- Required: run [scripts/register_task.py](../scripts/register_task.py); see [Task Registry instructions](../docs/KEY_DOCUMENTS.md#task-registry). -->
Task ID(s) registered in [logs/task_registry.jsonl](../logs/task_registry.jsonl):
Does this PR satisfy the six-task cycle rule? <!-- Yes/No -->

## Checklist
- [ ] Tests run <!-- Required: list tests run, e.g., `pytest` -->
- [ ] Docs updated <!-- Required: describe updates or state 'N/A' -->
- [ ] AGENTS.md instructions followed <!-- Required: confirm compliance with [AGENTS.md](../AGENTS.md) -->
- [ ] Absolute Protocol consulted <!-- Required: confirm reference to [docs/The_Absolute_Protocol.md](../docs/The_Absolute_Protocol.md) -->
- [ ] Co-creation framework checked <!-- Required: confirm alignment with `docs/co_creation_framework.md` -->
- [ ] AI ethics framework adhered <!-- Required: confirm principles in `docs/ai_ethics_framework.md` -->
- [ ] Change-justification statement included ("I did X on Y to obtain Z, expecting behavior B") <!-- Required: ensure Action Summary uses this format -->
- [ ] Key-document summaries verified (`scripts/verify_doc_hashes.py`) <!-- Required: run verification script -->
- [ ] Version bumps applied and `component_index.json` updated <!-- Required: confirm version synchronization -->
- [ ] Connector registry updated if connectors changed <!-- Required: update [CONNECTOR_INDEX.md](../docs/connectors/CONNECTOR_INDEX.md) -->
- [ ] Flow diagrams represented in Mermaid, not PNG/SVG <!-- Required: use Mermaid for any diagrams -->

## Connector Checklist
<!-- Select all connectors affected by this change -->
- [ ] operator_api
- [ ] operator_upload
- [ ] crown_ws
- [ ] webrtc
- [ ] open_web_ui
- [ ] telegram_bot
- [ ] primordials_api
- [ ] narrative_api

## Connector/Index updated?
- [ ] Index updated? <!-- Required: confirm component index and documentation index regenerated -->
- [ ] Nazarick agent registry & docs updated

