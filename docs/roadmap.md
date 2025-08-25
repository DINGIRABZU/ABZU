# Roadmap

This roadmap tracks progress toward the Spiral OS vision. See
[project_overview.md](project_overview.md) for context and
[developer_manual.md](developer_manual.md) for implementation notes.

## Chakra Upgrade Timeline

Each chakra upgrade is tracked through a GitHub milestone and a dedicated issue.
Use the milestone to group related work and reference the issue to monitor
progress.

| Chakra | Target Quarter | Milestone | Issue |
| --- | --- | --- | --- |
| Root | Q3 2024 | milestone/root-chakra-q3-2024 | #101 |
| Sacral | Q4 2024 | milestone/sacral-chakra-q4-2024 | #102 |
| Solar Plexus | Q1 2025 | milestone/solar-plexus-q1-2025 | #103 |
| Heart | Q2 2025 | milestone/heart-chakra-q2-2025 | #104 |
| Throat | Q3 2025 | milestone/throat-chakra-q3-2025 | #105 |
| Third Eye | Q4 2025 | milestone/third-eye-q4-2025 | #106 |
| Crown | Q1 2026 | milestone/crown-chakra-q1-2026 | #107 |

## Completed

- **Virtual environment manager** – unified script for venv creation and
  activation.
- **Sandbox repository** – isolated workspace for experiments.
- **`/sandbox` command** – spawns the sandbox repo during chat sessions.
- **Dependency installer** – fetches required packages on demand.
- **Rollback runner** – reverts a sandbox to the last good commit.

## Upcoming

- **Music command** enabling on‑the‑fly song generation.
- **Avatar lip‑sync** for more accurate mouth movement.
- **Expanded memory search** across cortex and vector layers.
- **Voice cloning** to mirror user tone within the sonic core.

## Future Enhancements

- **Community Discord channel** to coordinate contributors and gather feedback.
- **New style packs** expanding avatar and video generation aesthetics.
- **Hardware scaling strategy** for larger GPU clusters and edge devices.
- **Agent hardening** automating preflight fixes, watchdog recovery and triage summaries.

## Milestone Scores

The table below maps major milestones to their key components and current
component scores. Entries marked with ⚠️ indicate areas scoring below 7
that require additional attention. See [project_plan.md](project_plan.md) for
quarter‑level goals and owners.

| Milestone | Component | Score |
| --- | --- | --- |
| Music command | `music_generation.py` | ⚠️3 |
| Avatar lip‑sync | `ai_core/avatar/lip_sync.py` | ⚠️2 |
| Expanded memory search | `memory/cortex.py` | ⚠️1 |
| Expanded memory search | `vector_memory.py` | ⚠️3 |
| Voice cloning | `src/audio/voice_cloner.py` | ⚠️1 |

## Roadmap Maintenance

Review this roadmap after each chakra release to update milestone links,
issue references, and target quarters for remaining upgrades.
