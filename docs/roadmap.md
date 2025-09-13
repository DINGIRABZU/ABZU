# Roadmap

_Last updated: 2025-09-13_

This roadmap tracks progress toward the Spiral OS vision and outlines
milestone stages with target dates. See
[project_overview.md](project_overview.md) for context and
[developer_manual.md](developer_manual.md) for implementation notes.

## Milestone Stages

| Stage | Target Date |
| --- | --- |
| Prototype | 2024-07-01 |
| Alpha Release | 2024-10-01 |
| Beta Release | 2025-01-15 |
| General Availability | 2025-07-01 |

## Quarterly Chakra Targets

The project upgrades one chakra each quarter in the order below.

| Quarter | Chakra Focus |
| --- | --- |
| Q3 2024 | Root |
| Q4 2024 | Sacral |
| Q1 2025 | Solar Plexus |
| Q2 2025 | Heart |
| Q3 2025 | Throat |
| Q4 2025 | Third Eye |
| Q1 2026 | Crown |

Each chakra upgrade has a target quarter and is tracked through a GitHub
milestone and dedicated issue. Use the milestone to group related work,
reference the issue to monitor progress, and assign an owner accountable for
delivery.

| Chakra | Target Quarter | Milestone | Issue | Owner |
| --- | --- | --- | --- | --- |
| Root | Q3 2024 | root-chakra-q3-2024 | #101 | Mia |
| Sacral | Q4 2024 | sacral-chakra-q4-2024 | #102 | Liam |
| Solar Plexus | Q1 2025 | solar-plexus-q1-2025 | #103 | Ava |
| Heart | Q2 2025 | heart-chakra-q2-2025 | #104 | Noah |
| Throat | Q3 2025 | throat-chakra-q3-2025 | #105 | Zoe |
| Third Eye | Q4 2025 | third-eye-q4-2025 | #106 | Ethan |
| Crown | Q1 2026 | crown-chakra-q1-2026 | #107 | Sophia |

## Completed

- **Virtual environment manager** – unified script for venv creation and
  activation.
- **Sandbox repository** – isolated workspace for experiments.
- **`/sandbox` command** – spawns the sandbox repo during chat sessions.
- **Dependency installer** – fetches required packages on demand.
- **Rollback runner** – reverts a sandbox to the last good commit.

## Upcoming

- **Music command** enabling on‑the‑fly song generation and streaming output.
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
| Music command | `music_generation.py` (streaming support) | ⚠️4 |
| Avatar lip‑sync | `ai_core/avatar/lip_sync.py` | ⚠️2 |
| Expanded memory search | `memory/cortex.py` | ⚠️1 |
| Expanded memory search | `vector_memory.py` | ⚠️3 |
| Voice cloning | `src/audio/voice_cloner.py` | ⚠️1 |

## Roadmap Maintenance

Review and adjust this roadmap after each major release to update milestone
links, issue references, owner assignments, and target quarters for remaining
upgrades. Record each completed milestone's date here and add a corresponding
entry to `CHANGELOG.md`.
