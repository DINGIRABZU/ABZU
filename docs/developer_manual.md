# Developer Manual

This manual introduces the repository structure and the major runtime flows.
For a high level system map see
[architecture_overview.md](architecture_overview.md) and
[project_overview.md](project_overview.md).

## Repository layout
- `core/` – request routing, emotion analysis and model selection.
- `memory/` – persistent layers documented in
  [memory_architecture.md](memory_architecture.md).
- `cli/` and `tools/` – command line utilities and helper scripts.
- `docs/` – design references, including this manual and the
  [roadmap.md](roadmap.md).
- `tests/` – pytest suite guarding key behaviours.

## Crown–servant orchestration
The crown orchestrator launches specialised servant models and routes prompts
through them. `crown_prompt_orchestrator.py` selects a servant and
`servant_model_manager.py` handles lifecycle tasks. The process is summarised in
[architecture_overview.md](architecture_overview.md).

## Audio and visual pipeline
Text responses pass through `sonic_core_harmonics.md` for music generation and
`avatar_pipeline.md` for video rendering. `voice_aura.py` aligns spoken audio
with the avatar's expression. See `video_stream.py` for live output support.

## Sandbox self-modification flow
Developers experiment safely using the sandbox tools. The `/sandbox` command
creates an isolated repository, installs dependencies, and runs the rollback
runner to revert changes. This allows iterative self-modification without
polluting the main tree.
