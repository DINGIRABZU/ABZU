# Nazarick Agents

Nazarick hosts specialized servant agents aligned to chakra layers and coordinated by RAZAR and Crown.

## Agent Roster

| Agent ID | Role | Chakra Layer | Launch Command | Channel | Chakracon Telemetry |
| --- | --- | --- | --- | --- | --- |
| orchestration_master | Boot order and pipeline supervision | Crown | `./launch_servants.sh orchestration_master` | `#throne-room` | Prometheus `chakra_energy{chakra="crown"}` → `crown_overload` → notify `#throne-room` |
| prompt_orchestrator | Route prompts and recall context | Throat | `./launch_servants.sh crown_prompt_orchestrator` | `#signal-hall` | Prometheus `chakra_energy{chakra="throat"}` → `signal_hall_blockage` → page orchestration_master |
| qnl_engine | Process QNL sequences and insights | Third Eye | `./launch_servants.sh qnl_engine` | `#insight-observatory` | Prometheus `chakra_energy{chakra="third_eye"}` → `insight_drought` → route to `#throne-room` |
| memory_scribe | Persist transcripts and embeddings | Heart | `./launch_servants.sh memory_scribe` | `#memory-vault` | Prometheus `chakra_energy{chakra="heart"}` → `memory_backlog` → alert prompt_orchestrator |
| narrative_scribe | Render event bus stories | Throat | `./launch_servants.sh narrative_scribe` | `#story-forge` | Prometheus `narrative_rate` → `narrative_lag` → escalate to memory_scribe |

The registry lives at [agents/nazarick/agent_registry.json](../agents/nazarick/agent_registry.json). For the full channel hierarchy see [Nazarick Core Architecture](../agents/nazarick/nazarick_core_architecture.md).

## Launch Commands

Start all servants for development:

```bash
python start_dev_agents.py --all
```

Individual agents can be launched with `launch_servants.sh <agent_id>`.

## Channel Mapping

Agents publish to the channels shown above. The [Nazarick Web Console](nazarick_web_console.md) reads the registry and log files to display their status.

## UI Setup

Use the [Nazarick Web Console](nazarick_web_console.md) to monitor agents, open chat rooms, and issue commands. It loads `agents/nazarick/agent_registry.json` and `logs/nazarick_startup.json` to populate the agent panel.

## Cross-Links

- [Nazarick Guide](Nazarick_GUIDE.md)
- [Great Tomb of Nazarick](great_tomb_of_nazarick.md)

## Version History

| Version | Date | Notes |
| --- | --- | --- |
| [Unreleased](../CHANGELOG.md#documentation-audit) | - | Added agent roles, launch commands, channel mappings, chakra layers, and Chakracon telemetry. |
