# Nazarick Agents

Nazarick hosts specialized servant agents aligned to chakra layers and coordinated by RAZAR and Crown.

## Agent Roster

| Agent ID | Role | Launch Command | Channel |
| --- | --- | --- | --- |
| orchestration_master | Boot order and pipeline supervision | `./launch_servants.sh orchestration_master` | `#throne-room` |
| prompt_orchestrator | Route prompts and recall context | `./launch_servants.sh crown_prompt_orchestrator` | `#signal-hall` |
| qnl_engine | Process QNL sequences and insights | `./launch_servants.sh qnl_engine` | `#insight-observatory` |
| memory_scribe | Persist transcripts and embeddings | `./launch_servants.sh memory_scribe` | `#memory-vault` |

The registry lives at [agents/nazarick/agent_registry.json](../agents/nazarick/agent_registry.json).

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
| [Unreleased](../CHANGELOG.md#documentation-audit) | - | Added agent roles, launch commands, channel mappings, and UI setup. |
