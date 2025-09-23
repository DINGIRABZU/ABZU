# Onboarding Checklist

This checklist pairs with the [Neo‑ABZU Onboarding guide](../../NEOABZU/docs/onboarding.md); confirm both documents in `onboarding_confirm.yml`.

Follow this reading order before contributing. After reviewing each document, record its current SHA256 hash in `onboarding_confirm.yml` at the repository root for both APSU and Neo-APSU docs, and answer the questions in `onboarding_quiz.yml`.

Run `python docs/onboarding/wizard.py` to walk through repository setup. The wizard prompts for Neo-APSU document confirmations and writes signed summaries to `onboarding_confirm.yml`. CI runs `scripts/confirm_reading.py` and fails if required confirmations are missing.
A pre-commit hook also verifies that `onboarding_confirm.yml` references `docs/blueprint_spine.md`, `docs/The_Absolute_Protocol.md`, and `NEOABZU/docs/Oroboros_Core.md`.

The Crown router, RAG orchestrator, and Kimicho fallback now use Rust crates (`neoabzu_crown`, `neoabzu_rag`, `neoabzu_kimicho`); ensure these packages are installed as part of your environment setup.

1. [Project Overview](../project_overview.md)
2. [Architecture Overview](../architecture_overview.md)
3. [The Absolute Protocol](../The_Absolute_Protocol.md)
4. [Blueprint Spine](../blueprint_spine.md)
5. [Awakening Overview](../awakening_overview.md)
6. Module-specific guides relevant to your work:
   - [Vector Memory](../vector_memory.md)
   - [RAG Pipeline](../rag_pipeline.md)
   - [RAG Music Oracle](../rag_music_oracle.md)
   - [Vision System](../vision_system.md)
   - [Persona API Guide](../persona_api_guide.md)
   - [Spiral Cortex Terminal](../spiral_cortex_terminal.md)
   - [Narrative Framework](../narrative_framework.md)
   - [Narrative Engine Guide](../narrative_engine_GUIDE.md)
   - [Python Alpha Squad Dossier](python_alpha_squad.md) – subsystem leads, daily rituals, and escalation touchpoints for RAZAR boot ownership

7. [Arcade UI](../arcade_ui.md) – quickstart workflow and memory scan diagram
8. [Operator Quickstart](../operator_quickstart.md) – minimal setup and console usage
9. [Neo-APSU Onboarding](../../NEOABZU/docs/onboarding.md) – orientation for cross-project work
10. [OROBOROS Engine](../../NEOABZU/docs/OROBOROS_Engine.md), [OROBOROS Lexicon](../../NEOABZU/docs/OROBOROS_Lexicon.md), and [Migration Crosswalk](../../NEOABZU/docs/migration_crosswalk.md) – review engine mechanics, canonical glyphs, and Python↔Rust mapping
11. [First Consecrated Computation](../../NEOABZU/docs/Oroboros_Core.md#first-consecrated-computation) – narrative log of the inaugural ceremony

   - Review the Stage A automation entry points exposed by `operator_api`: `POST /alpha/stage-a1-boot-telemetry`, `POST /alpha/stage-a2-crown-replays`, and `POST /alpha/stage-a3-gate-shakeout`. Each endpoint records telemetry in `logs/stage_a/<run_id>/summary.json` for audit trails referenced by the roadmap and readiness reviews.

Confirm each item before starting code changes.

When submitting a pull request, ensure you can check:

- [ ] [AGENTS.md](../../AGENTS.md) instructions followed
- [ ] [The Absolute Protocol](../The_Absolute_Protocol.md) consulted
- [ ] Release notes updated in `CHANGELOG.md` and relevant component changelog(s)
- [ ] For connector additions: spec documented in [mcp_connectors.md](../mcp_connectors.md)
- [ ] `onboarding_confirm.yml` updated with SHA256 hashes for APSU and Neo-APSU docs
- [ ] `onboarding_quiz.yml` answers included in first pull request
- [ ] OROBOROS Engine, OROBOROS Lexicon, and migration_crosswalk acknowledged
