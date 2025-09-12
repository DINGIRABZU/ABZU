# Onboarding Checklist

Follow this reading order before contributing. After reviewing each document, record its current SHA256 hash in `onboarding_confirm.yml` at the repository root for both APZU and Neo-APZU docs, and answer the questions in `onboarding_quiz.yml`.

1. [Project Overview](../project_overview.md)
2. [Architecture Overview](../architecture_overview.md)
3. [The Absolute Protocol](../The_Absolute_Protocol.md)
4. [Blueprint Spine](../blueprint_spine.md)
5. Module-specific guides relevant to your work:
   - [Vector Memory](../vector_memory.md)
   - [RAG Pipeline](../rag_pipeline.md)
   - [RAG Music Oracle](../rag_music_oracle.md)
   - [Vision System](../vision_system.md)
   - [Persona API Guide](../persona_api_guide.md)
   - [Spiral Cortex Terminal](../spiral_cortex_terminal.md)

6. [Arcade UI](../arcade_ui.md) – quickstart workflow and memory scan diagram
7. [Operator Quickstart](../operator_quickstart.md) – minimal setup and console usage
8. [Neo-APZU Onboarding](../../NEOABZU/docs/onboarding.md) – orientation for cross-project work

Confirm each item before starting code changes.

When submitting a pull request, ensure you can check:

- [ ] [AGENTS.md](../../AGENTS.md) instructions followed
- [ ] [The Absolute Protocol](../The_Absolute_Protocol.md) consulted
- [ ] Release notes updated in `CHANGELOG.md` and relevant component changelog(s)
- [ ] `onboarding_confirm.yml` updated with SHA256 hashes for APZU and Neo-APZU docs
- [ ] `onboarding_quiz.yml` answers included in first pull request
