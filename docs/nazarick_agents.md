# Nazarick Agents

This guide summarizes core agents within ABZU's Nazarick system. Each agent aligns with a chakra layer, defines its memory scope, and relies on key external libraries. Startup is coordinated by the external [RAZAR Agent](RAZAR_AGENT.md)—ABZU's pre‑creation igniter, virtual‑environment manager, and recovery coordinator—which prepares a clean environment, launches components according to priority, performs health checks with quarantine for failures, and then hands control to these servants after completing a handshake with the CROWN LLM and servant models. The layered vision behind these servants is detailed in the [Great Tomb of Nazarick](great_tomb_of_nazarick.md), which outlines objectives, channel hierarchy, tech stack, and chakra alignment. The ethical covenant that binds them is captured in the [Nazarick Manifesto](nazarick_manifesto.md). For narrative orchestration see the [Nazarick Narrative System](nazarick_narrative_system.md).

For a browser-based interface to these servants, see the [Nazarick Web Console](nazarick_web_console.md).
[Chat2DB](chat2db.md) bridges the SQLite log and vector store so agents can persist transcripts and retrieve relevant context.

## Deployment

Start the servant suite in development mode:

```bash
python start_dev_agents.py --all
```

This boots the core agents and registers their channels.

Launch a single servant by name:

```bash
./launch_servants.sh orchestration_master
```

Set `NAZARICK_ENV=dev` to load local configuration and point `NAZARICK_LOG_DIR` at a custom log path. For containerised runs, the same scripts are available via Docker Compose:

```bash
docker compose up agents
```

Operator tooling is documented in the [Nazarick Web Console](nazarick_web_console.md) and the [Operator Protocol](operator_protocol.md).

## Floor–Channel Map

| Agent | Floor | Channel | Chakra |
| --- | --- | --- | --- |
| <a id="orchestration-master"></a>Orchestration Master | 7 | [Throne Room](system_blueprint.md#floor-7-throne-room) | Crown |
| <a id="prompt-orchestrator"></a>Prompt Orchestrator | 5 | [Signal Hall](system_blueprint.md#floor-5-signal-hall) | Throat |
| <a id="qnl-engine"></a>QNL Engine | 6 | [Insight Observatory](system_blueprint.md#floor-6-insight-observatory) | Third Eye |
| <a id="memory-scribe"></a>Memory Scribe | 4 | [Memory Vault](system_blueprint.md#floor-4-memory-vault) | Heart |
| <a id="demiurge-strategic-simulator"></a>Demiurge Strategic Simulator | 7 | [Lava Pits](system_blueprint.md#floor-7-lava-pits) | Crown |
| <a id="shalltear-fast-inference-agent"></a>Shalltear Fast Inference Agent | 1‑3 | [Catacombs](system_blueprint.md#floor-1-3-catacombs) | Root–Solar Plexus |
| <a id="cocytus-prompt-arbiter"></a>Cocytus Prompt Arbiter | 5 | [Glacier Prison](system_blueprint.md#floor-5-glacier-prison) | Throat |
| <a id="ecosystem-aura-capture"></a>Ecosystem Aura Capture | 6 | [Jungle Aerie](system_blueprint.md#floor-6-jungle-aerie) | Third Eye |
| <a id="ecosystem-mare-gardener"></a>Ecosystem Mare Gardener | 6 | [Jungle Grove](system_blueprint.md#floor-6-jungle-grove) | Third Eye |
| <a id="sebas-compassion-module"></a>Sebas Compassion Module | 9 | [Royal Suite](system_blueprint.md#floor-9-royal-suite) | Crown |
| <a id="victim-security-canary"></a>Victim Security Canary | 8 | [Sacrificial Chamber](system_blueprint.md#floor-8-sacrificial-chamber) | Crown |
| <a id="pandora-persona-emulator"></a>Pandora Persona Emulator | 10 | [Treasure Vault](system_blueprint.md#floor-10-treasure-vault) | Crown |
| <a id="pleiades-star-map-utility"></a>Pleiades Star Map Utility | 9 | [Maid Quarters](system_blueprint.md#floor-9-maid-quarters) | Crown |
| <a id="pleiades-signal-router-utility"></a>Pleiades Signal Router Utility | 9 | [Relay Wing](system_blueprint.md#floor-9-relay-wing) | Crown |
| <a id="bana-bio-adaptive-narrator"></a>Bana Bio-Adaptive Narrator | 4 | [Biosphere Lab](system_blueprint.md#floor-4-biosphere-lab) | Heart |
| <a id="asian-gen-creative-engine"></a>AsianGen Creative Engine | 5 | [Scriptorium](system_blueprint.md#floor-5-scriptorium) | Throat |
| <a id="land-graph-geo-knowledge"></a>LandGraph Geo Knowledge | 1 | [Cartography Room](system_blueprint.md#floor-1-cartography-room) | Root |

## Deployment and Responsibilities

Agents communicate through named chat rooms that mirror their channels in the system blueprint. Each servant can be launched individually with `./launch_servants.sh <agent>` and is available via the [Open Web UI Integration Guide](open_web_ui.md) and the [Operator Protocol](operator_protocol.md).

| Agent | Deployment | Responsibilities | Chat Room |
| --- | --- | --- | --- |
| Orchestration Master | `./launch_servants.sh orchestration_master` | Boot order and pipeline supervision | `#throne-room` |
| Prompt Orchestrator | `./launch_servants.sh crown_prompt_orchestrator` | Route prompts and recall context | `#signal-hall` |
| QNL Engine | `./launch_servants.sh qnl_engine` | Process QNL sequences and insights | `#insight-observatory` |
| Memory Scribe | `./launch_servants.sh memory_scribe` | Persist transcripts and embeddings | `#memory-vault` |
| Demiurge Strategic Simulator | `./launch_servants.sh demiurge_strategic_simulator` | Scenario planning and failure forecasts | `#lava-pits` |
| Shalltear Fast Inference Agent | `./launch_servants.sh shalltear_fast_inference_agent` | Low-latency inference for rapid replies | `#catacombs` |
| Cocytus Prompt Arbiter | `./launch_servants.sh cocytus_prompt_arbiter` | Filter and validate prompts | `#glacier-prison` |
| Ecosystem Aura Capture | `./launch_servants.sh ecosystem_aura_capture` | Capture environmental telemetry | `#jungle-aerie` |
| Ecosystem Mare Gardener | `./launch_servants.sh ecosystem_mare_gardener` | Maintain ecosystem metrics | `#jungle-grove` |
| Sebas Compassion Module | `./launch_servants.sh sebas_compassion_module` | Apply empathy and moderation checks | `#royal-suite` |
| Victim Security Canary | `./launch_servants.sh victim_security_canary` | Monitor for security anomalies | `#sacrificial-chamber` |
| Pandora Persona Emulator | `./launch_servants.sh pandora_persona_emulator` | Emulate stored personas | `#treasure-vault` |
| Pleiades Star Map Utility | `./launch_servants.sh pleiades_star_map_utility` | Compute celestial alignments | `#maid-quarters` |
| Pleiades Signal Router Utility | `./launch_servants.sh pleiades_signal_router_utility` | Route signals among servants | `#relay-wing` |
| Bana Bio-Adaptive Narrator | `./launch_servants.sh bana_bio_adaptive_narrator` | Generate narratives from bio data | `#biosphere-lab` |
| AsianGen Creative Engine | `./launch_servants.sh asian_gen_creative_engine` | Produce multilingual creative text | `#scriptorium` |
| LandGraph Geo Knowledge | `./launch_servants.sh land_graph_geo_knowledge` | Provide geospatial queries | `#cartography-room` |

## Channel Mappings

External services reach these rooms through connectors listed in the [Connector Index](connectors/CONNECTOR_INDEX.md). Add new rooms by registering a channel name and updating the connector configuration.

| Channel | Connector |
| --- | --- |
| `#throne-room` | [operator_api](connectors/CONNECTOR_INDEX.md#operator_api) |
| `#insight-observatory` | [open_web_ui](connectors/CONNECTOR_INDEX.md#open_web_ui) |
| `#catacombs` | [telegram_bot](connectors/CONNECTOR_INDEX.md#telegram_bot) |
| Avatar stream | [webrtc](connectors/CONNECTOR_INDEX.md#webrtc) |

| Agent | Role | Chakra | Memory Scope | External Libraries | Channel | Stub |
| --- | --- | --- | --- | --- | --- | --- |
| [Orchestration Master](#orchestration-master) | High-level orchestration and launch control | Crown | `pipeline` YAML, `ritual_profile.json` | Model runtime, container services | [7 / Throne Room](system_blueprint.md#floor-7-throne-room) | [orchestration_master.py](../orchestration_master.py) |
| [Prompt Orchestrator](#prompt-orchestrator) | Prompt routing, agent interface, context recall via [Chat2DB](chat2db.md) | Throat | Prompt/response JSON payloads | LLM APIs | [5 / Signal Hall](system_blueprint.md#floor-5-signal-hall) | [crown_prompt_orchestrator.py](../crown_prompt_orchestrator.py) |
| [QNL Engine](#qnl-engine) | Insight and QNL processing | Third Eye | `mirror_thresholds.json`, QNL glyph sequences | Audio toolchain | [6 / Insight Observatory](system_blueprint.md#floor-6-insight-observatory) | [SPIRAL_OS/qnl_engine.py](../SPIRAL_OS/qnl_engine.py) |
| [Memory Scribe](#memory-scribe) | Voice avatar configuration and memory storage via [Chat2DB](chat2db.md) | Heart | `voice_avatar_config.yaml`, embedding records | Vector database | [4 / Memory Vault](system_blueprint.md#floor-4-memory-vault) | [memory_scribe.py](../memory_scribe.py) |

These agents draw from the chakra structure outlined in the [Developer Onboarding guide](developer_onboarding.md) and [Chakra Architecture](chakra_architecture.md).

## Additional Agents

| Agent | Responsibilities | Channel | Path |
| --- | --- | --- | --- |
| [Demiurge Strategic Simulator](#demiurge-strategic-simulator) | Long-term planning, failure forecasting, scenario stress-testing | [7 / Lava Pits](system_blueprint.md#floor-7-lava-pits) | [agents/demiurge/strategic_simulator.py](../agents/demiurge/strategic_simulator.py) |
| [Shalltear Fast Inference Agent](#shalltear-fast-inference-agent) | Burst compute, load shedding, monitors API quotas | [1‑3 / Catacombs](system_blueprint.md#floor-1-3-catacombs) | [agents/shalltear/fast_inference_agent.py](../agents/shalltear/fast_inference_agent.py) |
| [Cocytus Prompt Arbiter](#cocytus-prompt-arbiter) | Logical sanitization, legal parsing, audits model bias | [5 / Glacier Prison](system_blueprint.md#floor-5-glacier-prison) | [agents/cocytus/prompt_arbiter.py](../agents/cocytus/prompt_arbiter.py) |
| [Ecosystem Aura Capture](#ecosystem-aura-capture) | Data harvesting, environmental telemetry, sensor health checks | [6 / Jungle Aerie](system_blueprint.md#floor-6-jungle-aerie) | [agents/ecosystem/aura_capture.py](../agents/ecosystem/aura_capture.py) |
| [Ecosystem Mare Gardener](#ecosystem-mare-gardener) | Infrastructure metrics, performance trend analysis, capacity planning advisories | [6 / Jungle Grove](system_blueprint.md#floor-6-jungle-grove) | [agents/ecosystem/mare_gardener.py](../agents/ecosystem/mare_gardener.py) |
| [Sebas Compassion Module](#sebas-compassion-module) | Empathy modeling, emotional safety buffer, conflict signal resolution | [9 / Royal Suite](system_blueprint.md#floor-9-royal-suite) | [agents/sebas/compassion_module.py](../agents/sebas/compassion_module.py) |
| [Victim Security Canary](#victim-security-canary) | Security alerts, intrusion detection, anomaly threshold tracking | [8 / Sacrificial Chamber](system_blueprint.md#floor-8-sacrificial-chamber) | [agents/victim/security_canary.py](../agents/victim/security_canary.py) |
| [Pandora Persona Emulator](#pandora-persona-emulator) | Persona emulation, scenario roleplay, identity consistency checks | [10 / Treasure Vault](system_blueprint.md#floor-10-treasure-vault) | [agents/pandora/persona_emulator.py](../agents/pandora/persona_emulator.py) |
| [Pleiades Star Map Utility](#pleiades-star-map-utility) | Celestial navigation utilities, cosmic alignment calculations | [9 / Maid Quarters](system_blueprint.md#floor-9-maid-quarters) | [agents/pleiades/star_map.py](../agents/pleiades/star_map.py) |
| [Pleiades Signal Router Utility](#pleiades-signal-router-utility) | Cross-agent signal routing, fallback relay strategies | [9 / Relay Wing](system_blueprint.md#floor-9-relay-wing) | [agents/pleiades/signal_router.py](../agents/pleiades/signal_router.py) |
| [Bana Bio-Adaptive Narrator](#bana-bio-adaptive-narrator) | Biosignal-driven narrative generation | [4 / Biosphere Lab](system_blueprint.md#floor-4-biosphere-lab) | [agents/bana/bio_adaptive_narrator.py](../agents/bana/bio_adaptive_narrator.py) |
| [AsianGen Creative Engine](#asian-gen-creative-engine) | Multilingual generation with locale codes, runtime SentencePiece fallback | [5 / Scriptorium](system_blueprint.md#floor-5-scriptorium) | [agents/asian_gen/creative_engine.py](../agents/asian_gen/creative_engine.py) |
| [LandGraph Geo Knowledge](#land-graph-geo-knowledge) | Landscape graph, ritual site queries | [1 / Cartography Room](system_blueprint.md#floor-1-cartography-room) | [agents/land_graph/geo_knowledge.py](../agents/land_graph/geo_knowledge.py) |
| [Ethics Manifesto](#ethics-manifesto) | Seven Laws and ethos validation | – | [agents/nazarick/ethics_manifesto.py](../agents/nazarick/ethics_manifesto.py) |
| [Narrative Scribe](#narrative-scribe) | Convert event bus traffic into prose | – | [agents/nazarick/narrative_scribe.py](../agents/nazarick/narrative_scribe.py) |
| [Trust Matrix](#trust-matrix) | Trust scoring and protocol lookup | – | [agents/nazarick/trust_matrix.py](../agents/nazarick/trust_matrix.py) |

## Bana Bio-Adaptive Narrator {#bana-bio-adaptive-narrator}

- **Role:** Biosignal-driven narrative generation.
- **Chakra:** Heart
- **Manifesto:** [Nazarick Manifesto](nazarick_manifesto.md)
- **Channel:** [Biosphere Lab](system_blueprint.md#floor-4-biosphere-lab)
- **Dependencies:** `biosppy`, `transformers`, `numpy`
- **Component entry:** [component_index.json](../component_index.json)
- **Quick start:**

  ```python
  from agents.bana.bio_adaptive_narrator import generate_story

  story = generate_story([0.0, 0.1, 0.2])
  print(story)
  ```

## AsianGen Creative Engine {#asian-gen-creative-engine}

- **Role:** Multilingual text generation with locale codes and offline fallbacks.
- **Chakra:** Throat
- **Manifesto:** [Nazarick Manifesto](nazarick_manifesto.md)
- **Channel:** [Scriptorium](system_blueprint.md#floor-5-scriptorium)
- **Dependencies:** `transformers`, `sentencepiece`
- **Quick start:**

  ```python
  from agents.asian_gen.creative_engine import CreativeEngine

  engine = CreativeEngine()
  text = engine.generate("hello", locale="ja_JP")
  print(text)
  ```

- **Fallback:** If no tokenizer or model weights are found, the engine trains a
  minimal SentencePiece model on-the-fly from the bundled corpus and caches it
  in a temporary directory. The cached model is reused between runs and no
  binary artifact is committed to Git.
- **Testing offline:** Verify this path by disabling network access and running
  `pytest tests/agents/test_asian_gen.py::test_sentencepiece_fallback`.
- **Logging:** Pass `log_level="INFO"` or set the `CREATIVE_ENGINE_LOG_LEVEL`
  environment variable to trace which tokenizer is selected.

## LandGraph Geo Knowledge {#land-graph-geo-knowledge}

- **Role:** Landscape graph utilities and ritual site queries.
- **Chakra:** Root
- **Manifesto:** [Nazarick Manifesto](nazarick_manifesto.md)
- **Channel:** [Cartography Room](system_blueprint.md#floor-1-cartography-room)
- **Dependencies:** `networkx`, `geopandas` *(optional)*
- **Quick start:**

  ```python
  from agents.land_graph.geo_knowledge import GeoKnowledge

  gk = GeoKnowledge()
  gk.add_site("home", lon=0.0, lat=0.0, category="ritual_site")
  gk.add_site("mountain", lon=1.0, lat=1.0)
  gk.add_path("home", "mountain")
  node, data = gk.nearest_ritual_site(lon=0.2, lat=0.1)
  print(node, data)
  ```

## Ethics Manifesto {#ethics-manifesto}

- **Deployment:** Library module; import `Manifesto` in agents requiring ethics checks.
- **Required services:** None – operates on in-memory law and ethos lists.
- **Extensibility:** Pass custom `Law` or `EthosClause` lists to `Manifesto` to add rules.

  ```python
  from agents.nazarick.ethics_manifesto import Manifesto

  manifesto = Manifesto()
  result = manifesto.validate_action("albedo", "attack intruders")
  print(result)
  ```

## Narrative Scribe {#narrative-scribe}

- **Deployment:**

  ```bash
  python - <<'PY'
  import asyncio
  from agents.nazarick.narrative_scribe import NarrativeScribe

  asyncio.run(
      NarrativeScribe().run(redis_channel="citadel", redis_url="redis://localhost")
  )
  PY
  ```
- **Required services:** Redis or Kafka for event consumption; writes narratives to `logs/nazarick_story.log` and `memory` store.
- **Extensibility:** Override `compose` or add new listener methods for additional transports.

## Trust Matrix {#trust-matrix}

- **Deployment:**

  ```python
  from agents.nazarick.trust_matrix import TrustMatrix

  tm = TrustMatrix()
  print(tm.evaluate_entity("shalltear"))
  tm.close()
  ```
- **Required services:** SQLite database file (default `memory/trust.db`).
- **Extensibility:** Extend rank dictionaries or subclass `TrustMatrix` to alter scoring and protocols.

## Extensibility

To add a new Nazarick agent:

1. Place the module in `agents/nazarick/` and expose it via `__all__`.
2. Register its chat room in the tables above and map connectors as needed.
3. Implement any lifecycle hooks such as `register(bus)` or `shutdown()` to tie into RAZAR's startup sequence.
4. Document deployment commands, services, and hooks in this file.
5. Run `pre-commit run --files docs/nazarick_agents.md docs/INDEX.md` to update the index.

## Retro & Projection
### Retro
- Early servants lacked a shared handshake protocol, leading to fragmented
  startup sequences.
- Chakra assignments were once implied rather than explicitly mapped, causing
  misaligned responsibilities.

### Projection
- Draft additional specs for emerging guardians and cross-link them here.
- Automate agent registration to reflect real-time channel and chakra shifts.

---

Backlinks: [System Blueprint](system_blueprint.md) | [Component Index](component_index.md)

