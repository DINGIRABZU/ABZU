# Nazarick Agents

This guide summarizes core agents within ABZU's Nazarick system. Each agent aligns with a chakra layer, defines its memory scope, and relies on key external libraries. Startup is coordinated by the external [RAZAR Agent](RAZAR_AGENT.md), which prepares a clean environment before these internal services come online.

| Agent | Role | Chakra | Memory Scope | External Libraries | Stub |
| --- | --- | --- | --- | --- | --- |
| Orchestration Master | High-level orchestration and launch control | Crown | `pipeline` YAML, `ritual_profile.json` | Model runtime, container services | [orchestration_master.py](../orchestration_master.py) |
| Prompt Orchestrator | Prompt routing and agent interface | Throat | Prompt/response JSON payloads | LLM APIs | [crown_prompt_orchestrator.py](../crown_prompt_orchestrator.py) |
| QNL Engine | Insight and QNL processing | Third Eye | `mirror_thresholds.json`, QNL glyph sequences | Audio toolchain | [SPIRAL_OS/qnl_engine.py](../SPIRAL_OS/qnl_engine.py) |
| Memory Scribe | Voice avatar configuration and memory storage | Heart | `voice_avatar_config.yaml`, embedding records | Vector database | [memory_scribe.py](../memory_scribe.py) |

These agents draw from the chakra structure outlined in the [Developer Onboarding guide](developer_onboarding.md) and [Chakra Architecture](chakra_architecture.md).

## Additional Agents

| Agent | Responsibilities | Path |
| --- | --- | --- |
| Demiurge Strategic Simulator | Long-term planning, failure forecasting, scenario stress-testing | [agents/demiurge/strategic_simulator.py](../agents/demiurge/strategic_simulator.py) |
| Shalltear Fast Inference Agent | Burst compute, load shedding, monitors API quotas | [agents/shalltear/fast_inference_agent.py](../agents/shalltear/fast_inference_agent.py) |
| Cocytus Prompt Arbiter | Logical sanitization, legal parsing, audits model bias | [agents/cocytus/prompt_arbiter.py](../agents/cocytus/prompt_arbiter.py) |
| Ecosystem Aura Capture | Data harvesting, environmental telemetry, sensor health checks | [agents/ecosystem/aura_capture.py](../agents/ecosystem/aura_capture.py) |
| Ecosystem Mare Gardener | Infrastructure metrics, performance trend analysis, capacity planning advisories | [agents/ecosystem/mare_gardener.py](../agents/ecosystem/mare_gardener.py) |
| Sebas Compassion Module | Empathy modeling, emotional safety buffer, conflict signal resolution | [agents/sebas/compassion_module.py](../agents/sebas/compassion_module.py) |
| Victim Security Canary | Security alerts, intrusion detection, anomaly threshold tracking | [agents/victim/security_canary.py](../agents/victim/security_canary.py) |
| Pandora Persona Emulator | Persona emulation, scenario roleplay, identity consistency checks | [agents/pandora/persona_emulator.py](../agents/pandora/persona_emulator.py) |
| Pleiades Star Map Utility | Celestial navigation utilities, cosmic alignment calculations | [agents/pleiades/star_map.py](../agents/pleiades/star_map.py) |
| Pleiades Signal Router Utility | Cross-agent signal routing, fallback relay strategies | [agents/pleiades/signal_router.py](../agents/pleiades/signal_router.py) |
| Bana Bio-Adaptive Narrator | Biosignal-driven narrative generation | [agents/bana/bio_adaptive_narrator.py](../agents/bana/bio_adaptive_narrator.py) |
| Asian Gen Creative Engine | Multilingual generation with locale codes, runtime SentencePiece fallback | [agents/asian_gen/creative_engine.py](../agents/asian_gen/creative_engine.py) |
| Land Graph Geo Knowledge | Landscape graph, ritual site queries | [agents/land_graph/geo_knowledge.py](../agents/land_graph/geo_knowledge.py) |

## Bana Bio-Adaptive Narrator

- **Role:** Biosignal-driven narrative generation.
- **Chakra:** Heart
- **Dependencies:** `biosppy`, `transformers`, `numpy`
- **Quick start:**

  ```python
  from agents.bana.bio_adaptive_narrator import generate_story

  story = generate_story([0.0, 0.1, 0.2])
  print(story)
  ```

## AsianGen Creative Engine

- **Role:** Multilingual text generation with locale codes and offline fallbacks.
- **Chakra:** Throat
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

## LandGraph Geo Knowledge

- **Role:** Landscape graph utilities and ritual site queries.
- **Chakra:** Root
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

