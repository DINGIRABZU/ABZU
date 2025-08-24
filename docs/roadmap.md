# Roadmap

This roadmap tracks progress toward the Spiral OS vision. See
[project_overview.md](project_overview.md) for context and
[developer_manual.md](developer_manual.md) for implementation notes.

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
