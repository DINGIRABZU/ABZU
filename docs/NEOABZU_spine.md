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

Stage B sonic rehearsals now require the audio stack guardrail introduced in
`start_spiral_os.py`: the bootstrap aborts when `python -m audio.check_env
--strict` reports missing FFmpeg, pydub or simpleaudio, enforcing
`AUDIO_BACKEND=pydub` before rehearsals continue. Operators install the pinned
`audio` extras bundle documented in [audio_stack.md](audio_stack.md) prior to
triggering the guardrail. The companion `scripts/setup_audio_env.sh` ritual
calls `modulation_arrangement.check_daw_availability` so missing Ardour or
Carla executables surface as warnings and rehearsal exports fall back to
audio-only renders until the DAWs land on PATH.

Vector memory updates now mirror this discipline: the fallback lattice keeps a NumPy cache so pure-Python search stays under the 120 ms P95 target during the 10 k-item ingestion drill. Update [scaling/vector_db_scaling_checklist.md](scaling/vector_db_scaling_checklist.md) whenever the benchmarks move.
Telemetry collectors now wrap `modulation_arrangement` and `src/audio/engine`
to emit JSON events during mixes, playback, and DAW fallbacks. Operators feed
the resulting stream into [monitoring/audio_rehearsal_telemetry.md](monitoring/audio_rehearsal_telemetry.md)
for Stage B readiness sign-off.

Neo‑APSU connector rehearsals mirror that discipline: the
[neo_apsu_connector_template](../connectors/neo_apsu_connector_template.py)
now emits an MCP capability payload described in
[mcp_capability_payload.md](connectors/mcp_capability_payload.md).
Stage B handshakes log the acknowledged contexts and session identifiers so
operators can reconcile rehearsal transcripts before heartbeats begin.
Doctrine compliance now enforces a three-part checklist before a connector
enters rehearsal: it must appear in `component_index.json` and
[CONNECTOR_INDEX.md](connectors/CONNECTOR_INDEX.md), its heartbeat schema must
align with [schemas/mcp_heartbeat_payload.schema.json](../schemas/mcp_heartbeat_payload.schema.json),
and its MCP rotation metadata must confirm the credential was refreshed within
the declared window. The most recent Stage B3 drill logged
`20250926T180300Z-PT48H` for the operator and Crown connectors (preceded by
`20250926T180231Z-PT48H`, `20250925T094604Z-PT48H`, the follow-up refresh
`20251024T174210Z-PT48H`, and the earlier `20250922T101554Z-PT48H` rehearsal) so auditors
can see every rotation window in [`logs/stage_b_rotation_drills.jsonl`](../logs/stage_b_rotation_drills.jsonl).【F:logs/stage_b_rotation_drills.jsonl†L24-L45】
The API now annotates those ledger entries with the rotation headline and any
credential expiry surfaced during the drill, letting Stage C readiness dashboards
render a human-readable status without scraping raw stdout.【F:operator_api.py†L470-L575】【F:operator_api.py†L640-L713】
`OperatorMCPAdapter` wraps `operator_api` and `operator_upload` in that
checklist, delegating the Stage B handshake and heartbeat to the template
helpers. The shared `scripts/stage_b_smoke.py` run exercises those adapters with
`crown_handshake` and appends credential rotation drills to
`logs/stage_b_rotation_drills.jsonl`. Production FastAPI deployments now
instantiate the shared adapter during startup so `/operator/command` and
`/operator/upload` reuse the stored session and emit background Stage B
heartbeats that log credential rotations when the gateway refreshes expiry
timestamps. The refresh also normalizes REST and trial gRPC handshakes, storing
trace bundles with checksum parity so Stage C diff artifacts inherit the same
NeoABZU vector contract evidence.【F:connectors/operator_mcp_adapter.py†L21-L170】【F:scripts/stage_b_smoke.py†L24-L230】【F:logs/stage_b_rotation_drills.jsonl†L1-L120】【F:operator_api.py†L470-L713】
Recent console work also exposes Stage A automation lanes directly through
`operator_api` (`POST /alpha/stage-a1-boot-telemetry`,
`/alpha/stage-a2-crown-replays`, `/alpha/stage-a3-gate-shakeout`), letting
operators trigger boot telemetry, replay capture, and gate shakeouts without
dropping into shell scripts while still producing the same `logs/stage_a/<run_id>/summary.json`
artifacts consumed by the roadmap and doctrine ledgers.
The same console lanes now cover Stage C by exposing `/alpha/stage-c1-exit-checklist`,
`/alpha/stage-c2-demo-storyline`, `/alpha/stage-c3-readiness-sync`, and
`/alpha/stage-c4-operator-mcp-drill` so operators can validate the exit checklist,
capture the scripted demo harness, merge Stage A/B readiness snapshots, and record
MCP drill evidence under `logs/stage_c/<run_id>/` without leaving the dashboard.
 Dedicated rehearsal modules ([operator_api_stage_b.py](../connectors/operator_api_stage_b.py),
 [operator_upload_stage_b.py](../connectors/operator_upload_stage_b.py), and
 [crown_handshake_stage_b.py](../connectors/crown_handshake_stage_b.py)) build on
 the shared helper to emit the canonical heartbeat payloads while keeping
 production adapters lean.

## Version History
- v0.1.2 (2025-10-09): Linked RAZAR blueprint spine to dedicated `KIMI2_API_KEY`,
  `AIRSTAR_API_KEY`, and `RSTAR_API_KEY` credentials documented in
  [SECURITY.md](SECURITY.md#remote-agent-credentials).
- v0.1.1 (2025-10-07): Documented blueprint synchronization requirements for architecture commits.
- v0.1.0 (2025-10-05): Documented identity spine pipeline.
