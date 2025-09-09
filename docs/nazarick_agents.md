# Nazarick Agents

Nazarick hosts specialized servant agents aligned to chakra layers and coordinated by RAZAR and Crown.

See [Nazarick Agent Profiles](nazarick_agent_profiles.md) for personality and expression details.

## Agent Roster

| Agent ID | Role | Chakra Layer | Launch Command | Channel | Chakracon Telemetry |
| --- | --- | --- | --- | --- | --- |
| orchestration_master | Boot order and pipeline supervision | Crown | `./launch_servants.sh orchestration_master` | `#throne-room` | Prometheus `chakra_energy{chakra="crown"}` → `crown_overload` → notify `#throne-room` |
| prompt_orchestrator | Route prompts and recall context | Throat | `./launch_servants.sh crown_prompt_orchestrator` | `#signal-hall` | Prometheus `chakra_energy{chakra="throat"}` → `signal_hall_blockage` → page orchestration_master |
| qnl_engine | Process QNL sequences and insights | Third Eye | `./launch_servants.sh qnl_engine` | `#insight-observatory` | Prometheus `chakra_energy{chakra="third_eye"}` → `insight_drought` → route to `#throne-room` |
| memory_scribe | Persist transcripts and embeddings | Heart | `./launch_servants.sh memory_scribe` | `#memory-vault` | Prometheus `chakra_energy{chakra="heart"}` → `memory_backlog` → alert prompt_orchestrator |
| narrative_scribe | Render event bus stories | Throat | `./launch_servants.sh narrative_scribe` | `#story-forge` | Prometheus `narrative_rate` → `narrative_lag` → escalate to memory_scribe |

The registry lives at [agents/nazarick/agent_registry.json](../agents/nazarick/agent_registry.json). For the full channel hierarchy see [Nazarick Core Architecture](../agents/nazarick/nazarick_core_architecture.md).

## Chakra Healing Agents

These guardians poll Chakracon metrics and invoke recovery scripts when thresholds are exceeded. See [Chakra Healing](chakra_healing.md) for script details.

| Agent | Script | Action |
| --- | --- | --- |
| `root_agent` | `scripts/chakra_healing/root_restore_network.sh` | Restart network interface or reduce disk I/O |
| `sacral_agent` | `scripts/chakra_healing/sacral_gpu_recover.py` | Reset GPU VRAM or pause GPU tasks |
| `solar_agent` | `scripts/chakra_healing/solar_cpu_throttle.py` | Cap runaway CPU processes via cgroups |
| `heart_agent` | `scripts/chakra_healing/heart_memory_repair.py` | Compact or purge memory layers |
| `throat_agent` | `scripts/chakra_healing/throat_api_stabilize.sh` | Adjust rate limits or restart gateway services |
| `third_eye_agent` | `scripts/chakra_healing/third_eye_inference_flush.py` | Clear model queue and hot-reload model |
| `crown_agent` | `scripts/chakra_healing/crown_full_restart.sh` | Orchestrate system reboot and operator notification |


### Narrative History Adapter

Each chakra agent can retrieve its recent narrative context using the shared
story adapter:

```python
from agents.utils.story_adapter import get_recent_stories

stories = get_recent_stories("root_agent", limit=20)
```

Streaming the full log is also supported:

```python
from agents.utils.story_adapter import watch_stories

watch_stories(print)
```


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
