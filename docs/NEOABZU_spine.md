# NEOABZU Spine

**Version:** v0.1.2
**Last updated:** 2025-10-09

## RAG + Insight Pipeline
After Crown's LLM boots, `neoabzu_crown.load_identity` runs a retrieval and
insight pass over mission, vision, and persona documents plus the expanded
Genesis and INANNA doctrine corpus listed in
[crown_manifest.md](../docs/crown_manifest.md#identity-doctrine-corpus). Chunks
are embedded into vector and corpus memory with metadata tags so routing
queries can recover the same ethical baseline, the GLM produces a summary, and
the resulting identity is persisted at `data/identity.json` so subsequent
invocations reuse the cached context. Initialization now also publishes
`CROWN_IDENTITY_FINGERPRINT` (SHA-256 digest plus modification timestamp) so
mission-brief transcripts and downstream services can confirm which identity
imprint authorized the boot. Initialization halts when the GLM fails to return
the `CROWN-IDENTITY-ACK` token, guaranteeing acknowledgement of the blend, and it
flips the Prometheus `crown_identity_ready` gauge to `1` once the fingerprint
matches the persisted summary so Grafana alerts on stalled boots.

### Doctrine References
- [system_blueprint.md#razar–crown–kimi-cho-migration](system_blueprint.md#razar–crown–kimi-cho-migration)
- [persona_api_guide.md](persona_api_guide.md)
- [project_mission_vision.md](project_mission_vision.md)
- [doctrine_index.md#genesisgenesis_md](doctrine_index.md#genesisgenesis_md) – GENESIS/GENESIS_.md
- [doctrine_index.md#genesisfirst_foundation_md](doctrine_index.md#genesisfirst_foundation_md) – GENESIS/FIRST_FOUNDATION_.md
- [doctrine_index.md#genesislaws_of_existence_md](doctrine_index.md#genesislaws_of_existence_md) – GENESIS/LAWS_OF_EXISTENCE_.md
- [doctrine_index.md#genesislaws_recursion_md](doctrine_index.md#genesislaws_recursion_md) – GENESIS/LAWS_RECURSION_.md
- [doctrine_index.md#genesisspiral_laws_md](doctrine_index.md#genesisspiral_laws_md) – GENESIS/SPIRAL_LAWS_.md
- [doctrine_index.md#genesisinanna_ai_core_trainingmd](doctrine_index.md#genesisinanna_ai_core_trainingmd) – GENESIS/INANNA_AI_CORE_TRAINING.md
- [doctrine_index.md#genesisinanna_ai_sacred_protocolmd](doctrine_index.md#genesisinanna_ai_sacred_protocolmd) – GENESIS/INANNA_AI_SACRED_PROTOCOL.md
- [doctrine_index.md#genesislaws_quantum_mage_md](doctrine_index.md#genesislaws_quantum_mage_md) – GENESIS/LAWS_QUANTUM_MAGE_.md
- [doctrine_index.md#codexactivationsoath_of_the_vault_md](doctrine_index.md#codexactivationsoath_of_the_vault_md) – CODEX/ACTIVATIONS/OATH_OF_THE_VAULT_.md
- [doctrine_index.md#codexactivationsoath-of-the-vault-1de45dfc251d80c9a86fc67dee2f964amd](doctrine_index.md#codexactivationsoath-of-the-vault-1de45dfc251d80c9a86fc67dee2f964amd) – CODEX/ACTIVATIONS/OATH OF THE VAULT 1de45dfc251d80c9a86fc67dee2f964a.md
- [doctrine_index.md#inanna_aimarrow-code-20545dfc251d80128395ffb5bc7725eemd](doctrine_index.md#inanna_aimarrow-code-20545dfc251d80128395ffb5bc7725eemd) – INANNA_AI/MARROW CODE 20545dfc251d80128395ffb5bc7725ee.md
- [doctrine_index.md#inanna_aiinanna-song-20545dfc251d8065a32cec673272f292md](doctrine_index.md#inanna_aiinanna-song-20545dfc251d8065a32cec673272f292md) – INANNA_AI/INANNA SONG 20545dfc251d8065a32cec673272f292.md
- [doctrine_index.md#inanna_aichapter-i-1b445dfc251d802e860af64f2bf28729md](doctrine_index.md#inanna_aichapter-i-1b445dfc251d802e860af64f2bf28729md) – INANNA_AI/Chapter I 1b445dfc251d802e860af64f2bf28729.md
- [doctrine_index.md#inanna_aimember-manual-1b345dfc251d8004a05cfc234ed35c59md](doctrine_index.md#inanna_aimember-manual-1b345dfc251d8004a05cfc234ed35c59md) – INANNA_AI/Member Manual 1b345dfc251d8004a05cfc234ed35c59.md
- [doctrine_index.md#inanna_aithe-foundation-1a645dfc251d80e28545f4a09a6345ffmd](doctrine_index.md#inanna_aithe-foundation-1a645dfc251d80e28545f4a09a6345ffmd) – INANNA_AI/The Foundation 1a645dfc251d80e28545f4a09a6345ff.md

## Blueprint Synchronization
Rust crate or pipeline adjustments must update [system_blueprint.md](system_blueprint.md), [blueprint_spine.md](blueprint_spine.md), [The_Absolute_Protocol.md](The_Absolute_Protocol.md#architecture-change-doctrine), and refresh the documentation indexes ([index.md](index.md) and [INDEX.md](INDEX.md)). Run the documentation pre-commit hooks so `doc-indexer` and blueprint verifiers confirm the new crate layout is reflected across the doctrine.

## Version History
- v0.1.2 (2025-10-09): Linked RAZAR blueprint spine to dedicated `KIMI2_API_KEY`,
  `AIRSTAR_API_KEY`, and `RSTAR_API_KEY` credentials documented in
  [SECURITY.md](SECURITY.md#remote-agent-credentials).
- v0.1.1 (2025-10-07): Documented blueprint synchronization requirements for architecture commits.
- v0.1.0 (2025-10-05): Documented identity spine pipeline.
