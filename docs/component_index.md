# Component Index

Generated automatically. Lists each Python and Rust file with its description and external dependencies.

| File | Language | Description | Dependencies |
| --- | --- | --- | --- |
| `INANNA_AI/AVATAR/avatar_builder/demo_lipsync.py` | Python | Generate a lip-synced avatar animation from text. | INANNA_AI, core |
| `INANNA_AI/__init__.py` | Python | Core package for the INANNA AI helpers. | None |
| `INANNA_AI/adaptive_learning.py` | Python | Adaptive learning agents for threshold and wording tuning. | core |
| `INANNA_AI/audio_emotion_listener.py` | Python | Capture microphone audio and estimate the speaker's emotion. | librosa, numpy, sounddevice |
| `INANNA_AI/context.py` | Python | Lightweight context memory for recent user prompts. | None |
| `INANNA_AI/corpus_memory.py` | Python | Simple embedding-based search across the corpus memory directories. | chromadb, crown_config, numpy, sentence_transformers |
| `INANNA_AI/db_storage.py` | Python | SQLite helpers to store voice interactions. | None |
| `INANNA_AI/defensive_network_utils.py` | Python | Defensive network helpers for monitoring and secure POST requests. | requests, scapy |
| `INANNA_AI/emotion_analysis.py` | Python | Lightweight emotion analysis tools using Librosa. | librosa, numpy, opensmile, torch, transformers |
| `INANNA_AI/emotional_memory.py` | Python | Simple JSONL log of emotional interactions for language models. | None |
| `INANNA_AI/emotional_synaptic_engine.py` | Python | Simple emotion-to-filter mapping with memory adjustment. | None |
| `INANNA_AI/ethical_validator.py` | Python | Validate user prompts before hitting the language model. | agents, numpy, sentence_transformers |
| `INANNA_AI/existential_reflector.py` | Python | Generate a short self-description using a placeholder GLM endpoint. | requests |
| `INANNA_AI/gate_orchestrator.py` | Python | Simple gate orchestrator translating text to/from complex vectors. | core, numpy, torch |
| `INANNA_AI/gates.py` | Python | Signature helpers for the RFA core. | cryptography |
| `INANNA_AI/glm_analyze.py` | Python | Analyze Python modules using a placeholder GLM endpoint. | INANNA_AI, requests |
| `INANNA_AI/glm_init.py` | Python | Summarize project purpose using a placeholder GLM endpoint. | INANNA_AI, requests |
| `INANNA_AI/glm_integration.py` | Python | Wrapper around a placeholder GLM-4.1V-9B endpoint. | aiohttp, requests |
| `INANNA_AI/learning/__init__.py` | Python | Utilities for fetching external learning data. | None |
| `INANNA_AI/learning/github_metadata.py` | Python | Fetch metadata for GitHub repositories. | crown_config, requests |
| `INANNA_AI/learning/github_scraper.py` | Python | Fetch README files from GitHub repositories. | crown_config, requests, sentence_transformers |
| `INANNA_AI/learning/project_gutenberg.py` | Python | Helpers for retrieving texts from Project Gutenberg. | bs4, crown_config, requests, sentence_transformers |
| `INANNA_AI/learning/training_guide.py` | Python | Parse the categorized INANNA training guide. | None |
| `INANNA_AI/listening_engine.py` | Python | Real-time microphone listening with basic feature extraction. | core, numpy |
| `INANNA_AI/love_matrix.py` | Python | Constants related to the Great Mother archetype. | None |
| `INANNA_AI/main.py` | Python | Command line interface for INANNA AI. | crown_router, learning, neoabzu_rag, numpy, personality_layers |
| `INANNA_AI/network_utils/__init__.py` | Python | Network monitoring utilities. | None |
| `INANNA_AI/network_utils/__main__.py` | Python | Command line entry for network utilities. | None |
| `INANNA_AI/network_utils/analysis.py` | Python | Basic traffic analysis for PCAP files. | scapy |
| `INANNA_AI/network_utils/capture.py` | Python | Packet capture helpers using scapy or pyshark. | scapy |
| `INANNA_AI/network_utils/config.py` | Python | Configuration helpers for network utilities. | None |
| `INANNA_AI/personality_layers/__init__.py` | Python | Personality layers for INANNA AI. | albedo |
| `INANNA_AI/personality_layers/albedo/__init__.py` | Python | Albedo personality layer combining state context with the GLM. | SPIRAL_OS |
| `INANNA_AI/personality_layers/albedo/alchemical_persona.py` | Python | State machine tracking alchemical progress and emotional metrics. | MUSIC_FOUNDATION, numpy |
| `INANNA_AI/personality_layers/albedo/enlightened_prompt.py` | Python | Helpers to compose prompts for Albedo's enlightened responses. | None |
| `INANNA_AI/personality_layers/albedo/glm_integration.py` | Python | Compatibility wrapper exposing :class:`~INANNA_AI.glm_integration.GLMIntegration`. | None |
| `INANNA_AI/personality_layers/albedo/state_contexts.py` | Python | Prompt templates for each alchemical state. | None |
| `INANNA_AI/personality_layers/citrinitas_layer.py` | Python | Illumination phase personality layer. | None |
| `INANNA_AI/personality_layers/nigredo_layer.py` | Python | Shadow phase personality layer. | None |
| `INANNA_AI/personality_layers/rubedo_layer.py` | Python | Completion phase personality layer. | None |
| `INANNA_AI/response_manager.py` | Python | Simple dialogue manager blending audio and text context. | None |
| `INANNA_AI/retrain_and_deploy.py` | Python | Automate fine-tuning and deployment of INANNA models. | crown_config, mlflow |
| `INANNA_AI/rfa_7d.py` | Python | Random Field Array 7D with quantum-like execution and DNA serialization. | numpy, qutip |
| `INANNA_AI/silence_reflection.py` | Python | Detect sustained silence and suggest a short meaning. | numpy |
| `INANNA_AI/sonic_emotion_mapper.py` | Python | Map emotional context to audio synthesis parameters. | yaml |
| `INANNA_AI/speaking_engine.py` | Python | Generate speech using gTTS with emotion-based style adjustments. | core, crown_config, numpy, tools |
| `INANNA_AI/speech_loopback_reflector.py` | Python | Analyze synthesized speech and update voice parameters. | None |
| `INANNA_AI/stt_whisper.py` | Python | Speech-to-text helpers using the Whisper library. | crown_config, whisper |
| `INANNA_AI/train_soul.py` | Python | Utilities for fine-tuning the :class:`RFA7D` core. | core, numpy |
| `INANNA_AI/tts_bark.py` | Python | Text-to-speech wrapper for Suno's Bark. | bark, numpy |
| `INANNA_AI/tts_coqui.py` | Python | Text-to-speech helpers using the Coqui TTS library. | TTS, numpy |
| `INANNA_AI/tts_tortoise.py` | Python | Text-to-speech wrapper for the Tortoise library. | numpy, tortoise |
| `INANNA_AI/tts_xtts.py` | Python | Text-to-speech wrapper for the XTTS model from Coqui TTS. | TTS, numpy |
| `INANNA_AI/utils.py` | Python | Utility helpers for audio processing and logging. | core, neoabzu_chakrapulse, numpy |
| `INANNA_AI/voice_evolution.py` | Python | Helpers to evolve INANNA's vocal style. | crown_config, numpy, yaml |
| `INANNA_AI/voice_layer_albedo.py` | Python | Voice modulation layer with alchemical tone presets. | None |
| `INANNA_AI_AGENT/__init__.py` | Python | Convenience imports and CLI exposure for the INANNA AI agent. | None |
| `INANNA_AI_AGENT/benchmark_preprocess.py` | Python | Benchmark preprocessing of INANNA AI source texts. | None |
| `INANNA_AI_AGENT/inanna_ai.py` | Python | Command line interface for the INANNA AI system. | INANNA_AI, SPIRAL_OS, yaml |
| `INANNA_AI_AGENT/model.py` | Python | Load local language models and tokenizers. | transformers |
| `INANNA_AI_AGENT/preprocess.py` | Python | Text preprocessing utilities for INANNA AI rituals. | markdown, numpy, sentence_transformers |
| `INANNA_AI_AGENT/source_loader.py` | Python | Utilities for reading ritual source texts. | None |
| `MUSIC_FOUNDATION/__init__.py` | Python | Utilities and helpers for the Music Foundation package. | None |
| `MUSIC_FOUNDATION/human_music_to_qnl_converter.py` | Python | human_music_to_qnl_converter.py | numpy |
| `MUSIC_FOUNDATION/inanna_music_COMPOSER_ai.py` | Python | inanna_music_COMPOSER_ai.py | MUSIC_FOUNDATION, librosa, numpy, soundfile, yaml |
| `MUSIC_FOUNDATION/layer_generators.py` | Python | Basic waveform generators for Spiral OS music layers. | librosa, numpy, soundfile |
| `MUSIC_FOUNDATION/music_foundation.py` | Python | music_foundation.py | librosa, numpy, soundfile |
| `MUSIC_FOUNDATION/qnl_utils.py` | Python | Shared utilities for converting music analysis into QNL data. | numpy, sentence_transformers |
| `MUSIC_FOUNDATION/seven_plane_analyzer.py` | Python | Analyze audio features across seven metaphysical planes. | essentia, librosa, numpy |
| `MUSIC_FOUNDATION/synthetic_stego.py` | Python | Simple LSB audio steganography utilities. | numpy, soundfile |
| `MUSIC_FOUNDATION/synthetic_stego_engine.py` | Python | Simple frequency-based steganography routines. | numpy |
| `NEOABZU/chakrapulse/src/lib.rs` | Rust | No description | crossbeam-channel, once_cell, pyo3 |
| `NEOABZU/core/src/lib.rs` | Rust | No description | neoabzu-narrative, opentelemetry, pyo3, ron, serde, tracing, tracing-opentelemetry |
| `NEOABZU/crown/src/lib.rs` | Rust | No description | neoabzu-chakrapulse, neoabzu-core, neoabzu-insight, neoabzu-memory, neoabzu-rag, pyo3 |
| `NEOABZU/fusion/src/lib.rs` | Rust | No description | pyo3, tracing |
| `NEOABZU/inanna/src/lib.rs` | Rust | No description | neoabzu-chakrapulse, pyo3 |
| `NEOABZU/insight/src/lib.rs` | Rust | No description | metrics, pyo3, tracing |
| `NEOABZU/k2coder/src/lib.rs` | Rust | No description | None |
| `NEOABZU/kimicho/src/lib.rs` | Rust | No description | neoabzu-instrumentation, once_cell, pyo3, reqwest, serde_json, tracing |
| `NEOABZU/memory/src/lib.rs` | Rust | No description | once_cell, opentelemetry, pyo3, tracing, tracing-opentelemetry |
| `NEOABZU/narrative/src/lib.rs` | Rust | No description | tracing |
| `NEOABZU/neoabzu/__init__.py` | Python | No description | None |
| `NEOABZU/neoabzu/vector.py` | Python | No description | grpc |
| `NEOABZU/neoabzu/vector_pb2.py` | Python | Generated protocol buffer code. | google |
| `NEOABZU/neoabzu/vector_pb2_grpc.py` | Python | Client and server classes corresponding to protobuf-defined services. | grpc |
| `NEOABZU/numeric/src/lib.rs` | Rust | No description | ndarray, numpy, pyo3 |
| `NEOABZU/persona/src/lib.rs` | Rust | No description | once_cell, pyo3, serde, serde_yaml |
| `NEOABZU/rag/src/lib.rs` | Rust | No description | neoabzu-memory, opentelemetry, pyo3, tracing, tracing-opentelemetry |
| `NEOABZU/razar/src/lib.rs` | Rust | No description | neoabzu-chakrapulse, pyo3 |
| `NEOABZU/vector/src/lib.rs` | Rust | No description | metrics, opentelemetry, prost, pyo3, serde, serde_json, sled, thiserror, tokio, tonic, tracing, tracing-opentelemetry |
| `NEOABZU/vector/tests/load_test.py` | Python | Simple load test for the vector gRPC service. | neoabzu |
| `NEOABZU/vector/tests/test_grpc_python.py` | Python | No description | grpc, pytest |
| `SPIRAL_OS/__init__.py` | Python | Expose Spiral OS components and dynamic helpers. | None |
| `SPIRAL_OS/qnl_engine.py` | Python | Utilities for converting hexadecimal input into QNL phrases and waveforms. | numpy |
| `SPIRAL_OS/symbolic_parser.py` | Python | Intent parser that maps symbolic input to Spiral OS actions. | INANNA_AI |
| `agents/__init__.py` | Python | Core agent packages for ABZU. | worlds |
| `agents/albedo/__init__.py` | Python | Albedo agent messaging utilities and vision hooks. | agents |
| `agents/albedo/messaging.py` | Python | Compose messages for Nazarick entities based on rank and trust. | albedo, yaml |
| `agents/albedo/trust.py` | Python | Trust adjustment and interaction logging for Albedo dialogues. | agents, albedo, memory |
| `agents/albedo/vision.py` | Python | Avatar selection hooks driven by YOLOE detections. | agents |
| `agents/asian_gen/__init__.py` | Python | Asian language creative agents. | agents |
| `agents/asian_gen/creative_engine.py` | Python | Creative engine for Asian language text generation. | sentencepiece, transformers |
| `agents/bana/__init__.py` | Python | Bana bio-adaptive narrator agent. | agents |
| `agents/bana/bio_adaptive_narrator.py` | Python | Bio-adaptive narrator using biosignal streams to craft stories. | biosppy, connectors, memory, numpy, prometheus_client, psutil, pynvml, requests, transformers |
| `agents/bana/inanna_bridge.py` | Python | Bridge structured INANNA interactions into Bana's narrative engine. | bana |
| `agents/chakra_healing/__init__.py` | Python | Chakra healing agent modules. | None |
| `agents/chakra_healing/base.py` | Python | Shared helpers for chakra healing agents. | agents, citadel, requests |
| `agents/chakra_healing/crown_agent.py` | Python | Monitor crown chakra metrics and orchestrate full system restart. | agents |
| `agents/chakra_healing/heart_agent.py` | Python | Monitor heart chakra metrics and repair memory layers. | agents |
| `agents/chakra_healing/root_agent.py` | Python | Monitor root chakra metrics and trigger network restoration. | agents |
| `agents/chakra_healing/sacral_agent.py` | Python | Monitor sacral chakra metrics and reset GPU tasks. | agents |
| `agents/chakra_healing/solar_agent.py` | Python | Monitor solar chakra metrics and throttle CPU. | agents |
| `agents/chakra_healing/third_eye_agent.py` | Python | Monitor third eye chakra metrics and flush inference queues. | agents |
| `agents/chakra_healing/throat_agent.py` | Python | Monitor throat chakra metrics and stabilize API throughput. | agents |
| `agents/cocytus/__init__.py` | Python | Cocytus agent modules. | agents |
| `agents/cocytus/prompt_arbiter.py` | Python | Cocytus prompt arbitration utilities. | requests |
| `agents/demiurge/__init__.py` | Python | Demiurge agent modules. | agents |
| `agents/demiurge/strategic_simulator.py` | Python | Responsibilities: | requests |
| `agents/ecosystem/__init__.py` | Python | Ecosystem monitoring agents. | None |
| `agents/ecosystem/aura_capture.py` | Python | Responsibilities: | requests |
| `agents/ecosystem/mare_gardener.py` | Python | Responsibilities: | requests |
| `agents/event_bus.py` | Python | Simple event bus helper for agents. | aiokafka, citadel, opentelemetry, redis, worlds |
| `agents/experience_replay.py` | Python | No description | memory |
| `agents/guardian.py` | Python | Shared utilities for guardian agents. | cocytus |
| `agents/interaction_log.py` | Python | No description | None |
| `agents/land_graph/__init__.py` | Python | Land graph utilities. | None |
| `agents/land_graph/geo_knowledge.py` | Python | Geo-referenced land graph utilities. | geopandas, networkx, shapely |
| `agents/nazarick/__init__.py` | Python | Nazarick agent package. | None |
| `agents/nazarick/avatar_resuscitator.py` | Python | NAZARICK agent restoring stalled avatar sessions. | agents, citadel |
| `agents/nazarick/chakra_observer.py` | Python | No description | agents, citadel |
| `agents/nazarick/chakra_resuscitator.py` | Python | NAZARICK agent repairing chakras after heartbeat failures. | agents, citadel, prometheus_client |
| `agents/nazarick/document_registry.py` | Python | No description | None |
| `agents/nazarick/ethics_manifesto.py` | Python | Ethics Manifesto for Nazarick agents. | None |
| `agents/nazarick/narrative_scribe.py` | Python | Narrative Scribe agent. | agents, aiokafka, citadel, memory, redis, yaml |
| `agents/nazarick/resuscitator.py` | Python | NAZARICK agent restarting failed peers via lifecycle events. | agents |
| `agents/nazarick/service_launcher.py` | Python | Start core Nazarick agents after the Crown handshake. | agents |
| `agents/nazarick/trust_matrix.py` | Python | Trust classification and protocol lookup for Nazarick entities. | None |
| `agents/operator_dispatcher.py` | Python | Operator command dispatcher with access controls and log mirroring. | None |
| `agents/pandora/__init__.py` | Python | Pandora persona agents. | agents |
| `agents/pandora/persona_emulator.py` | Python | Responsibilities: | requests |
| `agents/pleiades/__init__.py` | Python | Pleiades utility modules. | agents |
| `agents/pleiades/signal_router.py` | Python | Responsibilities: | requests |
| `agents/pleiades/star_map.py` | Python | Responsibilities: | requests |
| `agents/razar/__init__.py` | Python | RAZAR agents. | agents |
| `agents/razar/ai_invoker.py` | Python | RAZAR AI handover invocation helper. | None |
| `agents/razar/blueprint_synthesizer.py` | Python | Build a component dependency graph from Markdown blueprints. | networkx |
| `agents/razar/boot_orchestrator.py` | Python | Boot orchestrator for the RAZAR agent. | agents, monitoring, razar, src, yaml |
| `agents/razar/checkpoint_manager.py` | Python | Simple checkpoint manager for RAZAR components. | None |
| `agents/razar/cli.py` | Python | Command line utilities for RAZAR agents. | agents, memory |
| `agents/razar/code_repair.py` | Python | Automated module repair using LLM patch suggestions. | INANNA_AI, razar |
| `agents/razar/crown_link.py` | Python | Communication link between the RAZAR agent and CROWN. | websockets |
| `agents/razar/doc_sync.py` | Python | Synchronize key documentation after component changes. | razar |
| `agents/razar/health_checks.py` | Python | Health check routines for RAZAR runtime components. | prometheus_client, psutil, pynvml |
| `agents/razar/ignition_builder.py` | Python | Update ``docs/Ignition.md`` from the component priority registry. | yaml |
| `agents/razar/lifecycle_bus.py` | Python | Lifecycle message bus for RAZAR components. | aiokafka, redis |
| `agents/razar/mission_logger.py` | Python | Structured mission logger for RAZAR components. | None |
| `agents/razar/module_builder.py` | Python | Utilities for constructing new RAZAR modules. | None |
| `agents/razar/planning_engine.py` | Python | Planning engine module for razar. | networkx, yaml |
| `agents/razar/pytest_runner.py` | Python | Prioritized pytest runner for RAZAR. | pytest, yaml |
| `agents/razar/quarantine_manager.py` | Python | Utilities for quarantining failing components. | agents |
| `agents/razar/recovery_manager.py` | Python | Recovery manager using ZeroMQ for error handling. | zmq |
| `agents/razar/remote_loader.py` | Python | Download and load remote RAZAR agents at runtime. | git, requests |
| `agents/razar/retro_bootstrap.py` | Python | Rebuild RAZAR modules from documentation references. | None |
| `agents/razar/runtime_manager.py` | Python | RAZAR runtime manager. | razar, yaml |
| `agents/razar/state_validator.py` | Python | State file validation utilities for RAZAR. | jsonschema |
| `agents/razar/vision_adapter.py` | Python | Stream YOLOE detections into RAZAR's planning engine. | agents, numpy |
| `agents/sebas/__init__.py` | Python | Sebas compassion agents. | agents |
| `agents/sebas/compassion_module.py` | Python | Responsibilities: | requests |
| `agents/shalltear/__init__.py` | Python | Shalltear agent modules. | agents |
| `agents/shalltear/fast_inference_agent.py` | Python | Responsibilities: | requests |
| `agents/sidekick_helper.py` | Python | Minimal helper answering operator questions from the document registry. | agents, fastapi, prometheus_client |
| `agents/task_orchestrator.py` | Python | Dispatch tasks to agents based on capabilities and triggers. | citadel |
| `agents/utils/__init__.py` | Python | Utility helpers for agents. | None |
| `agents/utils/story_adapter.py` | Python | Adapters for retrieving narrative stories for agents. | memory |
| `agents/vanna_data.py` | Python | Vanna-powered data lookup agent. | agents, core, memory |
| `agents/victim/__init__.py` | Python | Victim security agents. | agents |
| `agents/victim/security_canary.py` | Python | Security canary for intrusion monitoring. | requests |
| `ai_core/__init__.py` | Python | Package initialization. | None |
| `ai_core/avatar/__init__.py` | Python | Avatar animation utilities. | None |
| `ai_core/avatar/expression_controller.py` | Python | Generate rudimentary facial landmarks based on dialogue cues. | None |
| `ai_core/avatar/lip_sync.py` | Python | Utilities for aligning phonemes with video frame indices. | None |
| `ai_core/avatar/ltx_avatar.py` | Python | Lightweight wrapper for an imaginary LTX distilled avatar model. | numpy |
| `ai_core/avatar/phonemes.py` | Python | Phoneme extraction utilities. | phonemizer |
| `ai_core/video_pipeline/__init__.py` | Python | Video processing pipeline components. | None |
| `ai_core/video_pipeline/ltx_video_processor.py` | Python | LTX video processing utilities. | None |
| `ai_core/video_pipeline/pipeline.py` | Python | Video generation pipeline that selects processors based on a ``StyleConfig``. | style_engine |
| `ai_core/video_pipeline/pusa_v1_processor.py` | Python | Pusa V1 video processing utilities. | None |
| `albedo/__init__.py` | Python | Core types for albedo state machine. | None |
| `albedo/state_machine.py` | Python | State machine driven by trust and entity category. | None |
| `api/__init__.py` | Python | ABZU API package. | None |
| `api/memory_introspect.py` | Python | FastAPI application exposing memory introspection endpoints. | fastapi, prometheus_fastapi_instrumentator, src |
| `archetype_feedback_loop.py` | Python | Analyze spiral memory to suggest archetype shifts. | memory |
| `archetype_shift_engine.py` | Python | Determine when to switch personality layers based on ritual cues or emotion. | None |
| `aspect_processor.py` | Python | Utility functions for aspect analysis and logging. | None |
| `auto_retrain.py` | Python | Automatically trigger fine-tuning based on feedback metrics. | INANNA_AI, core, llm_api, mlflow, yaml |
| `bana/__init__.py` | Python | Bana utilities. | None |
| `bana/event_structurizer.py` | Python | Translate Bana interactions into schema-validated events. | jsonschema |
| `bana/narrative.py` | Python | Emit structured Bana narrative events. | agents, albedo, memory |
| `bana/narrative_api.py` | Python | HTTP API for retrieving Bana narratives and memory metadata. | fastapi, memory, prometheus_client, pydantic |
| `benchmarks/chat_gateway_benchmark.py` | Python | Benchmark message routing through the chat gateway. | communication |
| `benchmarks/llm_throughput_benchmark.py` | Python | Benchmark transformer throughput in tokens per second. | torch |
| `benchmarks/memory_store_benchmark.py` | Python | Benchmark basic memory store operations. | None |
| `benchmarks/pyo3_call_latency.py` | Python | No description | None |
| `benchmarks/query_memory_bench.py` | Python | Benchmark concurrent memory queries. | memory |
| `benchmarks/run_benchmarks.py` | Python | Run all benchmark scripts and report their metrics. | None |
| `benchmarks/rust_vs_python_path.py` | Python | No description | neoabzu_chakrapulse |
| `benchmarks/train_infer.py` | Python | Benchmark a minimal training and inference step. | torch |
| `chakracon/__init__.py` | Python | Chakra consultation utilities. | None |
| `chakracon/api.py` | Python | API for chakra metrics and advice logging. | fastapi, pydantic, requests |
| `citadel/__init__.py` | Python | Event infrastructure for agents. | None |
| `citadel/event_processor.py` | Python | FastAPI service that processes agent events. | aiokafka, asyncpg, fastapi, neo4j, prometheus_fastapi_instrumentator, redis |
| `citadel/event_producer.py` | Python | Interfaces for emitting agent events to message brokers. | aiokafka, redis |
| `communication/__init__.py` | Python | Package initialization. | None |
| `communication/floor_channel_socket.py` | Python | Socket.IO server managing floor and channel rooms. | socketio |
| `communication/gateway.py` | Python | Message gateway normalizing inputs from communication channels. | httpx |
| `communication/telegram_bot.py` | Python | Telegram bot forwarding messages to the avatar. | connectors, telegram |
| `communication/webrtc_gateway.py` | Python | Unified WebRTC gateway supporting FastAPI and MediaSoup. | aiortc, communication, core, fastapi, mediasoup, numpy, soundfile, src |
| `communication/webrtc_server.py` | Python | Compatibility layer exposing :mod:`communication.webrtc_gateway`. | None |
| `connectors/__init__.py` | Python | Communication connectors for Spiral OS. | None |
| `connectors/avatar_broadcast.py` | Python | Broadcast avatar frames to Discord and Telegram. | agents, tools |
| `connectors/base.py` | Python | Connector mixins and base classes. | None |
| `connectors/heart_mediator.py` | Python | Heart mediator routing Head↔Base communications. | None |
| `connectors/mcp_gateway_example.py` | Python | Minimal MCP-based connector example. | httpx |
| `connectors/message_formatter.py` | Python | No description | None |
| `connectors/narrative_mcp.py` | Python | MCP wrapper for narrative logging. | httpx |
| `connectors/neo_apsu_connector_template.py` | Python | Neo-APSU connector template. | httpx |
| `connectors/primordials_api.py` | Python | Minimal connector for sending metrics to the Primordials service. | None |
| `connectors/primordials_mcp.py` | Python | MCP wrapper for Primordials metrics. | httpx |
| `connectors/signal_bus.py` | Python | Simple signal bus for cross-connector messaging. | kafka, redis |
| `connectors/webrtc_connector.py` | Python | WebRTC connector for streaming data, audio, and video. | aiortc, communication, fastapi |
| `corpus_memory_logging.py` | Python | Append and read JSONL interaction records for corpus memory usage. | None |
| `crown/src/lib.rs` | Rust | No description | metrics, neoabzu-instrumentation, neoabzu-memory, pyo3, tracing |
| `crown_config/__init__.py` | Python | Load application configuration from environment variables. | pydantic, pydantic_settings |
| `crown_config/settings/__init__.py` | Python | Utilities for reading optional layer configuration. | yaml |
| `crown_decider.py` | Python | Heuristics for selecting a language model in the Crown agent. | INANNA_AI, audio, crown_config |
| `crown_prompt_orchestrator.py` | Python | Lightweight prompt orchestrator for the Crown console. | INANNA_AI, audio, core, memory |
| `data/biosignals/__init__.py` | Python | Biosignal dataset hashes and helpers. | None |
| `datpars/__init__.py` | Python | Placeholder package for DATPars utilities. | None |
| `datpars/interfaces.py` | Python | Stub interfaces for DATPars parsers. | None |
| `deployment/__init__.py` | Python | Package initialization. | None |
| `distributed_memory.py` | Python | No description | boto3, redis |
| `docs/onboarding/wizard.py` | Python | Interactive quick-start wizard for ABZU. | yaml |
| `download_model.py` | Python | Download DeepSeek-R1 weights from Hugging Face. | dotenv, huggingface_hub |
| `download_models.py` | Python | CLI utilities for downloading model weights and dependencies. | dotenv, huggingface_hub, requests, transformers |
| `emotion_registry.py` | Python | Persist emotional state and expose retrieval helpers. | None |
| `emotional_state.py` | Python | Manage emotional and soul state persistence. | cryptography |
| `env_validation.py` | Python | Environment variable validation utilities. | None |
| `examples/ritual_demo.py` | Python | Minimal emotion→music→insight demonstration. | audio, memory, simpleaudio |
| `examples/vision_wall_demo.py` | Python | Minimal 2D→3D vision pipeline demonstration. | imageio, numpy, src |
| `fusion/src/lib.rs` | Rust | No description | neoabzu-instrumentation, tracing |
| `glm_shell.py` | Python | Send shell commands to the Crown GLM endpoint. | INANNA_AI, agents, crown_config |
| `init_crown_agent.py` | Python | Initialize the crown agent and optional vector memory subsystem. | INANNA_AI, prometheus_client, requests, yaml |
| `insight_compiler.py` | Python | Aggregate interaction logs into an insight matrix. | jsonschema, requests |
| `instrumentation/src/lib.rs` | Rust | No description | opentelemetry, opentelemetry_sdk, tracing, tracing-opentelemetry, tracing-subscriber |
| `introspection_api.py` | Python | FastAPI service exposing an endpoint to return the AST of a module. | fastapi, prometheus_fastapi_instrumentator, pydantic, src |
| `invocation_engine.py` | Python | Pattern-based invocation engine. | neoabzu_rag, prometheus_client |
| `labs/__init__.py` | Python | Experimental modules and demonstrations. | None |
| `labs/cortex_sigil.py` | Python | Map sigils to actions or emotion modifiers. | None |
| `language_model_layer.py` | Python | Helpers for preparing language model insights for spoken summaries. | None |
| `learning_mutator.py` | Python | Suggest mutations to the intent matrix based on insight metrics. | None |
| `logging_filters.py` | Python | Enrich log records with emotional context. | None |
| `mcp/gateway.py` | Python | Model Context Protocol gateway. | connectors, mcp, starlette |
| `memory/__init__.py` | Python | Memory subsystem package. | agents, opentelemetry, worlds |
| `memory/bundle.py` | Python | Thin wrapper around the Rust memory bundle. | neoabzu_memory |
| `memory/chakra_registry.py` | Python | Chakra-aware registry built on top of :mod:`vector_memory`. | None |
| `memory/context_env.py` | Python | No description | core |
| `memory/cortex.py` | Python | Lightweight spiral memory stored as JSON lines. | worlds |
| `memory/cortex_cli.py` | Python | Command line utilities for managing spiral memory. | None |
| `memory/emotional.py` | Python | Persist and query emotional feature vectors in SQLite. | dlib, opentelemetry, transformers, worlds |
| `memory/mental.py` | Python | Neo4j-backed task memory with optional reinforcement learning hooks. | core, crown_config, opentelemetry |
| `memory/music_memory.py` | Python | Persistent store for music embedding vectors with emotion labels. | numpy |
| `memory/narrative_engine.py` | Python | Persistent narrative memory engine. | chromadb, core, opentelemetry, prometheus_client, psutil, pynvml |
| `memory/optional/__init__.py` | Python | Fallback implementations for optional memory layers and utilities like search. | None |
| `memory/optional/cortex.py` | Python | Fallback cortex layer returning empty results. | None |
| `memory/optional/emotional.py` | Python | No-op emotional layer used when the real implementation is unavailable. | None |
| `memory/optional/mental.py` | Python | No-op mental layer used when the real implementation is unavailable. | None |
| `memory/optional/music_memory.py` | Python | No-op music memory layer used when the real implementation is unavailable. | None |
| `memory/optional/narrative_engine.py` | Python | No-op narrative layer used when the real implementation is unavailable. | None |
| `memory/optional/sacred.py` | Python | No-op sacred glyph generator when torch or Pillow are unavailable. | None |
| `memory/optional/search.py` | Python | Fallback search module that returns no results. | None |
| `memory/optional/search_api.py` | Python | Fallback search API returning no results. | None |
| `memory/optional/spiral_memory.py` | Python | No-op spiral memory used when the real implementation is unavailable. | None |
| `memory/optional/spiritual.py` | Python | No-op spiritual layer used when the real implementation is unavailable. | None |
| `memory/optional/vector_memory.py` | Python | No-op vector memory used when the real implementation is unavailable. | None |
| `memory/query_memory.py` | Python | Aggregate memory queries across cortex, vector store and spiral layers. | optional |
| `memory/sacred.py` | Python | VAE-based sacred memory module using PyTorch. | PIL, torch |
| `memory/search.py` | Python | Unified memory search across multiple subsystems. | memory |
| `memory/search_api.py` | Python | Aggregate memory queries across layers with recency and source ranking. | memory |
| `memory/spiral_cortex.py` | Python | Store retrieval insights for the spiral cortex. | None |
| `memory/spiritual.py` | Python | SQLite-backed event ↔ symbol memory. | opentelemetry |
| `memory/story_lookup.py` | Python | No description | None |
| `memory/tracing.py` | Python | No description | opentelemetry |
| `memory/trust_registry.py` | Python | Entity classification with trust scoring and persistence. | None |
| `memory_scribe.py` | Python | Interface for recording embeddings in vector memory. | None |
| `memory_store.py` | Python | FAISS-backed in-memory vector store with SQLite persistence. | faiss, numpy, opentelemetry |
| `ml/__init__.py` | Python | Machine learning utilities and pipelines. | None |
| `ml/archetype_cluster.py` | Python | Cluster spiral memory vectors into archetypal groups. | MUSIC_FOUNDATION, numpy, sklearn |
| `ml/data_pipeline.py` | Python | Download text sources and optionally embed them. | INANNA_AI |
| `ml/emotion_classifier.py` | Python | Train and apply a simple emotion classifier using scikit-learn. | INANNA_AI, joblib, numpy, sklearn |
| `ml/evaluate_emotion_models.py` | Python | Evaluate pretrained emotion models on a labelled dataset. | INANNA_AI |
| `modulation_arrangement.py` | Python | Arrange and export audio stems produced by :mod:`vocal_isolation`. | audio |
| `monitoring/__init__.py` | Python | Monitoring utilities. | None |
| `monitoring/agent_heartbeat.py` | Python | Track agent heartbeat events and detect outages. | agents |
| `monitoring/agent_status_endpoint.py` | Python | Expose agent heartbeat summaries. | fastapi |
| `monitoring/avatar_watchdog.py` | Python | Avatar session watchdog emitting events when streams stall. | agents |
| `monitoring/chakra_heartbeat.py` | Python | Record chakra heartbeat timestamps and report synchronization status. | agents, citadel, prometheus_client |
| `monitoring/chakra_status_board.py` | Python | Expose chakra heartbeat frequencies and component versions. | agents, fastapi, prometheus_client |
| `monitoring/chakra_status_endpoint.py` | Python | Expose chakra heartbeat data and component versions. | agents, fastapi, prometheus_client |
| `monitoring/chakra_watchdog.py` | Python | Chakra heartbeat watchdog emitting events when chakras fall silent. | agents, prometheus_client |
| `monitoring/escalation_notifier.py` | Python | No description | None |
| `monitoring/heartbeat_logger.py` | Python | No description | agents, citadel |
| `monitoring/self_healing_endpoint.py` | Python | Expose self-healing ledger snapshots and stream updates. | fastapi |
| `monitoring/self_healing_ledger.py` | Python | No description | None |
| `monitoring/watchdog.py` | Python | Resource watchdog exposing Prometheus metrics for key services. | os_guardian, prometheus_client, psutil |
| `music_generation.py` | Python | Generate music from a text prompt using various models. | src, transformers |
| `music_llm_interface.py` | Python | Interface between the music analysis pipeline and LLM CROWN. | INANNA_AI, neoabzu_rag, numpy, src |
| `narrative_api.py` | Python | HTTP API for logging and retrieving persistent stories. | fastapi, memory, prometheus_client, pydantic |
| `nazarick-console/backend` | Rust | No description | axum, futures, neoabzu-chakrapulse, tokio, tracing, tracing-subscriber |
| `neoabzu_chakrapulse/__init__.py` | Python | Test stub for neoabzu_chakrapulse crate. | None |
| `nlq_api.py` | Python | NLQ API powered by Vanna AI. | agents, core, fastapi |
| `numeric/src/lib.rs` | Rust | No description | nalgebra, neoabzu-instrumentation, pyo3, tracing |
| `operator_api.py` | Python | Operator command API exposing the :class:`OperatorDispatcher`. | agents, bana, fastapi, memory, razar, scripts |
| `operator_service/__init__.py` | Python | Operator service exposing ignition, query, and status APIs. | None |
| `operator_service/api.py` | Python | FastAPI app exposing ignition, query, and status controls. | fastapi, memory, prometheus_fastapi_instrumentator, razar |
| `orchestration_master.py` | Python | High-level orchestrator selecting agents and wiring memory stores. | memory, scripts, tools, yaml |
| `os_guardian/__init__.py` | Python | Utilities for operating system automation. | None |
| `os_guardian/action_engine.py` | Python | Wrappers around OS input automation and browser control. | pyautogui, selenium |
| `os_guardian/cli.py` | Python | Command line interface for OS Guardian. | None |
| `os_guardian/perception.py` | Python | Screen capture and GUI detection utilities. | cv2, numpy, pyautogui, pytesseract, ultralytics |
| `os_guardian/planning.py` | Python | LangChain-based planner turning instructions into tool sequences. | langchain |
| `os_guardian/safety.py` | Python | Permission checks and rollback helpers for OS Guardian actions. | None |
| `persona/src/lib.rs` | Rust | No description | neoabzu-instrumentation, pyo3, tracing |
| `pipeline/__init__.py` | Python | Pipeline utilities for audio analysis. | None |
| `pipeline/music_analysis.py` | Python | High-level music analysis pipeline combining feature and emotion extraction. | INANNA_AI, audio, numpy |
| `prompt_engineering.py` | Python | Prompt transformations based on style presets. | style_engine |
| `rag/__init__.py` | Python | Retrieval-augmented generation helpers. | None |
| `rag/embedder.py` | Python | Embed RAG text chunks with optional sentiment tags. | INANNA_AI, crown_config, numpy, sentence_transformers |
| `rag/engine.py` | Python | Retrieval helper for vector memory documents. | haystack, llama_index |
| `rag/music_oracle.py` | Python | Music oracle that mixes RAG search with audio emotion analysis. | INANNA_AI, audio |
| `rag/parser.py` | Python | Utility to parse directories into text chunks for RAG. | None |
| `rag/src/lib.rs` | Rust | No description | metrics, neoabzu-instrumentation, neoabzu-memory, pyo3, tracing |
| `razar/__init__.py` | Python | Razar package hosting boot orchestration utilities. | None |
| `razar/__main__.py` | Python | Command line utilities for operating the RAZAR lifecycle bus. | agents |
| `razar/adaptive_orchestrator.py` | Python | Adaptive orchestrator that searches for efficient boot sequences. | yaml |
| `razar/ai_invoker.py` | Python | High level wrapper for remote RAZAR agents. | agents, tools |
| `razar/boot_orchestrator.py` | Python | Simple boot orchestrator reading a JSON component configuration. | agents, memory, neoabzu_core, neoabzu_kimicho, opentelemetry |
| `razar/bootstrap_utils.py` | Python | Utility constants shared across RAZAR bootstrap modules. | None |
| `razar/checkpoint_manager.py` | Python | Checkpoint utilities for the adaptive orchestrator. | None |
| `razar/cocreation_planner.py` | Python | Planner that consolidates blueprints, failures, and Crown suggestions. | yaml |
| `razar/crown_handshake.py` | Python | WebSocket handshake between RAZAR and the CROWN stack. | websockets |
| `razar/crown_link.py` | Python | WebSocket link between RAZAR and the CROWN agent. | websockets |
| `razar/doc_sync.py` | Python | Synchronize Ignition, blueprint and component docs. | agents, yaml |
| `razar/environment_builder.py` | Python | Environment builder for RAZAR. | yaml |
| `razar/health_checks.py` | Python | Health check routines for Razar boot components. | neoabzu_chakrapulse |
| `razar/issue_analyzer.py` | Python | Simple heuristics for classifying failure logs. | None |
| `razar/mission_logger.py` | Python | Lightweight proxy to :mod:`agents.razar.mission_logger`. | None |
| `razar/module_sandbox.py` | Python | Temporary sandbox for module patches from CROWN. | None |
| `razar/quarantine_manager.py` | Python | Utilities for quarantining failing components. | None |
| `razar/recovery_manager.py` | Python | Basic recovery manager coordinating shutdown, patching and resumption. | agents |
| `razar/status_dashboard.py` | Python | Simple CLI dashboard reporting boot status and quarantine information. | razar, yaml |
| `recursive_emotion_router.py` | Python | Recursive cycle through emotional processing stages. | labs, memory |
| `release.py` | Python | Release utilities for the project. | None |
| `ritual_trainer.py` | Python | Fine-tune the model from retrieval insights. | core, memory |
| `rstar_service/app.py` | Python | No description | fastapi, pydantic, rstar |
| `run_song_demo.py` | Python | Demo runner for INANNA Music Composer AI. | MUSIC_FOUNDATION, yaml |
| `scripts/__init__.py` | Python | Helper scripts for maintenance and testing. | None |
| `scripts/albedo_demo.py` | Python | Command line demo for Albedo persona interactions. | agents |
| `scripts/audit_doctrine.py` | Python | No description | None |
| `scripts/boot_sequence.py` | Python | No description | razar |
| `scripts/bootstrap.py` | Python | Bootstrap the development environment. | torch |
| `scripts/bootstrap_memory.py` | Python | Initialize all memory layers and report readiness. | memory |
| `scripts/bootstrap_world.py` | Python | Initialize mandatory layers, start Crown, and report readiness. | agents, memory, worlds |
| `scripts/build_component_index.py` | Python | Generate the component index. | None |
| `scripts/build_index.py` | Python | Build a Markdown index of repository modules, classes, and functions. | None |
| `scripts/capture_failing_tests.py` | Python | Run pytest and record failing cases for documentation. | None |
| `scripts/chakra_healing/heart_memory_repair.py` | Python | Compact or purge memory layers. | None |
| `scripts/chakra_healing/sacral_gpu_recover.py` | Python | Reset GPU VRAM or pause GPU tasks. | None |
| `scripts/chakra_healing/solar_cpu_throttle.py` | Python | Cap runaway CPU processes via cgroups. | None |
| `scripts/chakra_healing/third_eye_inference_flush.py` | Python | Clear model queue and hot-reload model. | None |
| `scripts/check_blueprints_and_tests.py` | Python | Fail CI when crates change without doc or test updates. | None |
| `scripts/check_component_index_json.py` | Python | Wrapper to validate component_index.json. | None |
| `scripts/check_connector_index.py` | Python | Ensure touched connectors have registry entries. | None |
| `scripts/check_connectors.py` | Python | Scan connectors for placeholder markers and missing MCP adoption. | None |
| `scripts/check_dependency_registry.py` | Python | Wrapper to validate docs/dependency_registry.md. | None |
| `scripts/check_env.py` | Python | Fail if required tools or packages are missing. | None |
| `scripts/check_key_documents.py` | Python | Verify that key documents exist. | yaml |
| `scripts/check_mcp_connectors.py` | Python | Verify connectors use MCP instead of raw HTTP endpoints. | None |
| `scripts/check_memory_layers.py` | Python | Verify memory layers respond with ready bootstrap data. | memory |
| `scripts/check_neoabzu_onboarding.py` | Python | Ensure onboarding_confirm.yml updated when NEOABZU code changes. | None |
| `scripts/check_no_binaries.py` | Python | Fail if any staged files are detected as binary. | None |
| `scripts/check_placeholders.py` | Python | Fail if files contain TODO or FIXME placeholders. | None |
| `scripts/component_inventory.py` | Python | Collect metadata for each Python component in the repository. | None |
| `scripts/confirm_reading.py` | Python | Ensure required onboarding documents have been read. | yaml |
| `scripts/data_validate.py` | Python | Validate training data schema using TensorFlow Data Validation. | tensorflow_data_validation |
| `scripts/dependency_check.py` | Python | Verify package imports and optional dependencies. | None |
| `scripts/ensure_blueprint_sync.py` | Python | Verify blueprint doc updates accompany core code changes. | None |
| `scripts/escalation_notifier.py` | Python | Monitor logs for recurring errors and escalate via operator command. | requests |
| `scripts/export_coverage.py` | Python | Export coverage metrics to component_index.json, | None |
| `scripts/generate_protocol_task.py` | Python | Create protocol refinement task after enough registry entries. | None |
| `scripts/generate_sbom.py` | Python | Generate a CycloneDX software bill of materials. | None |
| `scripts/health_check_connectors.py` | Python | Ping registered connectors and report readiness. | requests |
| `scripts/ingest_biosignal_events.py` | Python | Ingest biosignal CSV files as structured narrative events. | data, memory |
| `scripts/ingest_biosignals.py` | Python | Ingest biosignal CSV files into the narrative engine. | data, memory |
| `scripts/ingest_biosignals_jsonl.py` | Python | Ingest biosignals jsonl module for scripts. | data, memory |
| `scripts/ingest_ethics.py` | Python | Reindex ethics corpus files into the Chroma vector store. | INANNA_AI |
| `scripts/ingest_music_books.py` | Python | Ingest music theory books into the vector memory. | pdfplumber, unstructured |
| `scripts/ingest_sample_events.py` | Python | Ingest sample events into each memory layer and verify retrieval. | memory |
| `scripts/init_memory_layers.py` | Python | Bootstrap cortex, emotional, mental, spiritual and narrative stores. | memory |
| `scripts/list_layers.py` | Python | Print configured personality layers and whether they are enabled. | yaml |
| `scripts/log_intent.py` | Python | Append commit intent entries to the change ledger. | None |
| `scripts/manage_servants.py` | Python | No description | requests |
| `scripts/offsite_backup.py` | Python | Manage snapshot and restoration of off-site memory backups. | None |
| `scripts/quality_score.py` | Python | Compute quality scores for repository components. | None |
| `scripts/record_feedback.py` | Python | Log user feedback to the local database. | INANNA_AI |
| `scripts/recovery_daemon.py` | Python | No description | razar |
| `scripts/register_task.py` | Python | Append completed task details to the task registry. | None |
| `scripts/replay_state.py` | Python | Restore backups and rebuild vector memory from log files. | None |
| `scripts/require_connector_registry_update.py` | Python | Ensure connector registry updates accompany connector changes. | None |
| `scripts/require_module_docs.py` | Python | Require changelog and component index updates when new modules are added. | None |
| `scripts/require_onboarding_update.py` | Python | Fail if key documents change without updating onboarding confirmation. | None |
| `scripts/scan_todo_fixme.py` | Python | Fail if staged code contains TODO or FIXME markers. | None |
| `scripts/schedule_doc_audit.py` | Python | Audit key documents and log overdue reviews. | None |
| `scripts/self_heal_cycle.py` | Python | No description | razar |
| `scripts/show_emotion_glyph.py` | Python | Display the last recorded emotion with its spiral glyph. | None |
| `scripts/sign_release.py` | Python | Generate SHA256 checksums for build artifacts and sign them with GPG. | None |
| `scripts/snapshot_state.py` | Python | No description | None |
| `scripts/train_distributed.py` | Python | Distributed training example using PyTorch FSDP. | mlflow, omegaconf, optuna, torch |
| `scripts/update_error_index.py` | Python | Parse logs and append new errors to docs/error_registry.md. | None |
| `scripts/validate_absolute_protocol_checklist.py` | Python | No description | None |
| `scripts/validate_api_schemas.py` | Python | Validate API schemas against the FastAPI application. | jsonschema, openapi_spec_validator, src |
| `scripts/validate_change_justification.py` | Python | Verify pull requests include a Change Justification statement. | None |
| `scripts/validate_component_index.py` | Python | Ensure docs/component_index.md has no empty descriptions. | None |
| `scripts/validate_component_index_json.py` | Python | Validate status and ADR fields in component_index.json. | jsonschema |
| `scripts/validate_components.py` | Python | Validate registered component versions against requirements files. | None |
| `scripts/validate_configs.py` | Python | Validate YAML templates and JSON/YAML schema files. | jsonschema, yaml |
| `scripts/validate_docs.py` | Python | Validate documentation registry versions and cross-links. | None |
| `scripts/validate_ignition.py` | Python | Validate ignition module for scripts. | None |
| `scripts/validate_links.py` | Python | Validate Markdown links for broken or outdated targets. | None |
| `scripts/validate_schemas.py` | Python | Validate JSON files against their JSON Schemas. | jsonschema |
| `scripts/validate_world_registry.py` | Python | Validate world registry entries against existing components. | agents, memory, worlds |
| `scripts/vast_check.py` | Python | Check that the server is healthy and ready on Vast.ai. | aiortc, httpx |
| `scripts/verify_blueprint_refs.py` | Python | Ensure system_blueprint.md references all Rust crates. | None |
| `scripts/verify_chakra_monitoring.py` | Python | Verify chakra monitoring setup and metric emission. | agents |
| `scripts/verify_component_maturity.py` | Python | Verify modules have corresponding tests and docs. | None |
| `scripts/verify_crate_refs.py` | Python | No description | None |
| `scripts/verify_dependencies.py` | Python | Validate dependencies against docs/dependency_registry.md. | None |
| `scripts/verify_doc_hashes.py` | Python | Ensure protected documents have up-to-date hashes and summary fields. | yaml |
| `scripts/verify_doc_refs.py` | Python | No description | None |
| `scripts/verify_doc_summaries.py` | Python | Check onboarding doc summaries stay in sync with file hashes. | yaml |
| `scripts/verify_docs_up_to_date.py` | Python | No description | None |
| `scripts/verify_doctrine.py` | Python | No description | None |
| `scripts/verify_doctrine_refs.py` | Python | No description | None |
| `scripts/verify_ip_tags.py` | Python | Validate that all `@ip-sensitive` files appear in the IP registry. | None |
| `scripts/verify_milestone_operator_copresence.py` | Python | Run milestone checks for operator copresence. | None |
| `scripts/verify_onboarding_refs.py` | Python | Ensure onboarding_confirm.yml references required foundational documents. | yaml |
| `scripts/verify_release_signature.py` | Python | Verify release artifact checksums and signatures. | None |
| `scripts/verify_self_healing.py` | Python | Verify self-healing health checks. | None |
| `scripts/verify_versions.py` | Python | Compare module versions against component_index.json. | None |
| `scripts/welcome_banner.py` | Python | Utility script to print a cuneiform greeting before serving the page. | None |
| `scripts/world_export.py` | Python | Export current world configuration and patch metadata. | worlds |
| `servant_model_manager.py` | Python | Registry and launcher for auxiliary language models. | tools |
| `server.py` | Python | Minimal FastAPI server exposing health and utility endpoints. | INANNA_AI, PIL, agents, communication, connectors, core, crown_config, fastapi, memory, monitoring, numpy, prometheus_client, prometheus_fastapi_instrumentator, pydantic, yaml |
| `seven_dimensional_music.py` | Python | Utility for simple seven-dimensional music features. | MUSIC_FOUNDATION, numpy, src |
| `soul_state_manager.py` | Python | Track the active archetype and soul state transitions. | None |
| `spiral_embedder.py` | Python | CLI helper for inserting embeddings into ``spiral_vector_db``. | spiral_vector_db |
| `spiral_memory.py` | Python | Cross-layer spiral memory with recursive recall and event registry. | memory, opentelemetry, torch |
| `spiral_vector_db/__init__.py` | Python | Simple wrapper around ChromaDB for storing text embeddings. | MUSIC_FOUNDATION, chromadb, numpy |
| `src/__init__.py` | Python | Top-level package exposing core submodules. | None |
| `src/api/__init__.py` | Python | Package initialization. | None |
| `src/api/memory_introspect.py` | Python | Memory introspection endpoints. | fastapi |
| `src/api/server.py` | Python | FastAPI server providing video generation and avatar streaming APIs. | audio, fastapi, prometheus_fastapi_instrumentator, style_engine |
| `src/audio/__init__.py` | Python | Audio processing utilities and playback helpers. | None |
| `src/audio/audio_ingestion.py` | Python | Audio ingestion module for audio. | demucs, essentia, librosa, numpy, spleeter, torch, transformers |
| `src/audio/backends.py` | Python | Audio playback backends. | core, numpy, simpleaudio, soundfile |
| `src/audio/check_env.py` | Python | Diagnostic CLI to verify audio dependencies are installed. | None |
| `src/audio/dsp_engine.py` | Python | Basic audio DSP utilities primarily using ffmpeg. | magenta, numpy, rave, soundfile, torch |
| `src/audio/emotion_params.py` | Python | Emotion to music parameter resolution helpers. | INANNA_AI, MUSIC_FOUNDATION |
| `src/audio/engine.py` | Python | Simple playback engine for ritual loops and voice audio. | MUSIC_FOUNDATION, audio, numpy, pydub, simpleaudio, soundfile |
| `src/audio/mix_tracks.py` | Python | Utility script for mixing audio files. | MUSIC_FOUNDATION, numpy, soundfile, yaml |
| `src/audio/play_ritual_music.py` | Python | Compose short ritual music based on emotion and play it. | numpy, yaml |
| `src/audio/segment.py` | Python | Minimal audio segment abstraction with optional NumPy backend. | core, numpy |
| `src/audio/stego.py` | Python | Steganography helpers for ritual music. | MUSIC_FOUNDATION, numpy |
| `src/audio/voice_aura.py` | Python | Apply reverb and timbre effects based on the current emotion. | audio, soundfile |
| `src/audio/voice_cloner.py` | Python | Clone a user's voice using the optional EmotiVoice library. | INANNA_AI, core, numpy |
| `src/audio/waveform.py` | Python | Waveform synthesis utilities. | MUSIC_FOUNDATION, numpy, soundfile |
| `src/bin/vector_client.py` | Python | Command-line client for the NeoABZU vector service. | neoabzu |
| `src/cli.py` | Python | Unified command line interface for Spiral OS tools. | pytest, requests |
| `src/cli/__init__.py` | Python | Command-line interface utilities. | None |
| `src/cli/console_interface.py` | Python | Interactive REPL for the Crown agent. | INANNA_AI, audio, bana, core, memory, neoabzu_rag, prompt_toolkit, requests, tools |
| `src/cli/music_helper.py` | Python | Utility functions for handling music generation commands. | INANNA_AI, tools |
| `src/cli/sandbox_helper.py` | Python | Run code patches in an isolated sandbox and execute tests. | tools |
| `src/cli/spiral_cortex_terminal.py` | Python | Command line tool for exploring ``cortex_memory_spiral.jsonl``. | memory |
| `src/cli/voice.py` | Python | Command line tool to synthesize speech and play or stream it. | INANNA_AI, connectors, core, cv2, httpx, numpy |
| `src/cli/voice_clone.py` | Python | CLI for recording samples and synthesizing speech via :mod:`EmotiVoice`. | audio |
| `src/cli/voice_clone_helper.py` | Python | Helper for voice cloning within the console interface. | INANNA_AI, audio |
| `src/core/__init__.py` | Python | Core package exposing primary services. | None |
| `src/core/avatar_expression_engine.py` | Python | Synchronise avatar expressions with audio playback. | audio, core, numpy |
| `src/core/code_introspector.py` | Python | Utilities for inspecting repository code. | None |
| `src/core/config.py` | Python | Validated configuration loading using Pydantic. | pydantic, yaml |
| `src/core/context_tracker.py` | Python | Simple runtime context flags. | None |
| `src/core/contracts.py` | Python | Protocol definitions for cross-module services. | None |
| `src/core/emotion_analyzer.py` | Python | Mood tracking and emotion analysis utilities. | INANNA_AI |
| `src/core/expressive_output.py` | Python | Coordinate speech synthesis, playback and avatar frames. | audio, imageio, numpy |
| `src/core/facial_expression_controller.py` | Python | Basic facial expression control utilities. | numpy |
| `src/core/feedback_logging.py` | Python | Manage feedback logs and thresholds with on-disk persistence. | crown_config |
| `src/core/language_engine.py` | Python | Speech synthesis wrapper that optionally routes audio via a connector. | INANNA_AI |
| `src/core/memory_logger.py` | Python | Wrapper around corpus memory logging helpers. | None |
| `src/core/memory_physical.py` | Python | Storage utilities for raw physical inputs. | core, soundfile |
| `src/core/model_selector.py` | Python | Model selection and benchmarking utilities. | INANNA_AI |
| `src/core/self_correction_engine.py` | Python | Self-correct emotional output using recent feedback. | INANNA_AI, numpy |
| `src/core/task_parser.py` | Python | Simple text command parser returning structured intents. | None |
| `src/core/task_profiler.py` | Python | Task profiling helpers. | None |
| `src/core/utils/optional_deps.py` | Python | Helpers for optional dependencies with lightweight stubs. | None |
| `src/core/utils/seed.py` | Python | Utilities for deterministic behaviour. | numpy, torch |
| `src/core/video_engine.py` | Python | Avatar video generation utilities. | core, lwm, numpy |
| `src/dashboard/__init__.py` | Python | Dashboard components for monitoring and mixing. | None |
| `src/dashboard/app.py` | Python | Streamlit dashboard for visualising LLM performance. | pandas, streamlit |
| `src/dashboard/qnl_mixer.py` | Python | Tools for mixing QNL audio inside Streamlit. | MUSIC_FOUNDATION, audio, librosa, matplotlib, numpy, soundfile, streamlit |
| `src/dashboard/rl_metrics.py` | Python | Streamlit dashboard for reinforcement learning metrics. | INANNA_AI, pandas, streamlit |
| `src/dashboard/system_monitor.py` | Python | System resource monitoring utilities. | psutil |
| `src/dashboard/usage.py` | Python | Streamlit dashboard for usage metrics. | core, pandas, streamlit |
| `src/feedback_logging.py` | Python | Compatibility wrapper for :mod:`core.feedback_logging`. | core |
| `src/health/__init__.py` | Python | Health check utilities for Spiral OS. | None |
| `src/health/boot_diagnostics.py` | Python | Boot diagnostics for verifying essential services. | None |
| `src/health/essential_services.py` | Python | List of core modules required for Spiral OS boot diagnostics. | None |
| `src/init_crown_agent.py` | Python | Load Crown agent configuration and expose model endpoints. | worlds, yaml |
| `src/lwm/__init__.py` | Python | Large World Model package. | None |
| `src/lwm/config_model.py` | Python | Configuration model for the Large World Model. | omegaconf |
| `src/lwm/large_world_model.py` | Python | Minimal Large World Model converting 2D frames into a 3D scene. | None |
| `src/media/__init__.py` | Python | Unified media interfaces for audio, video, and avatar. | None |
| `src/media/audio/__init__.py` | Python | Audio generation and playback interface. | None |
| `src/media/audio/backends.py` | Python | Utilities for loading optional audio backends. | None |
| `src/media/audio/base.py` | Python | Audio-specific media processing interfaces. | None |
| `src/media/audio/generation.py` | Python | Audio generation utilities with optional dependencies. | pydub |
| `src/media/audio/playback.py` | Python | Audio playback utilities with optional dependencies. | ffmpeg |
| `src/media/avatar/__init__.py` | Python | Avatar generation and playback interface. | None |
| `src/media/avatar/base.py` | Python | Avatar-specific media processing interfaces. | None |
| `src/media/avatar/generation.py` | Python | Avatar generation utilities composed from audio and video. | audio, lwm, video |
| `src/media/avatar/lwm_renderer.py` | Python | No description | core, librosa, lwm, numpy |
| `src/media/avatar/playback.py` | Python | Avatar playback utilities. | audio, video |
| `src/media/base.py` | Python | Common media processing interfaces. | None |
| `src/media/video/__init__.py` | Python | Video generation and playback interface. | None |
| `src/media/video/base.py` | Python | Video-specific media processing interfaces. | None |
| `src/media/video/generation.py` | Python | Video generation utilities with optional dependencies. | ffmpeg, lwm |
| `src/media/video/playback.py` | Python | Video playback utilities with optional dependencies. | ffmpeg |
| `src/spiral_os/__init__.py` | Python | Spiral OS package providing command-line tools. | None |
| `src/spiral_os/__main__.py` | Python | Command-line interface for Spiral OS utilities. | yaml |
| `src/spiral_os/_hf_stub.py` | Python | Minimal stub of the `huggingface_hub` package used in tests. | None |
| `src/spiral_os/chakra_cycle.py` | Python | Chakra gear ratios with persistent heartbeat scheduler. | None |
| `src/spiral_os/pulse_emitter.py` | Python | Emit periodic heartbeat events for all chakras. | agents |
| `src/spiral_os/start_spiral_os.py` | Python | Launch the Spiral OS initialization sequence. | INANNA_AI, INANNA_AI_AGENT, connectors, core, dashboard, neoabzu_rag, tools, uvicorn, yaml |
| `start_crown_console.py` | Python | Run Crown services and video stream with graceful shutdown. | dotenv |
| `start_dev_agents.py` | Python | Command line launcher for the development agent cycle. | agents, memory, tools |
| `start_spiral_os.py` | Python | Launch the Spiral OS initialization sequence. | INANNA_AI, INANNA_AI_AGENT, connectors, core, dashboard, health, neoabzu_rag, tools, uvicorn, yaml |
| `state_transition_engine.py` | Python | Simple finite state engine based on emotional cues. | INANNA_AI |
| `style_engine/__init__.py` | Python | Package initialization. | None |
| `style_engine/neural_style_transfer.py` | Python | Simple neural style transfer utilities. | numpy |
| `style_engine/style_library.py` | Python | Utilities for loading video style configurations. | yaml |
| `task_profiling.py` | Python | Compatibility wrappers around :class:`core.task_profiler.TaskProfiler`. | core |
| `tests/INANNA_AI/__init__.py` | Python | No description | None |
| `tests/INANNA_AI/test_origin_ingestion.py` | Python | Ensure reindex embeds Marrow Code and Inanna Song. | INANNA_AI |
| `tests/__init__.py` | Python | No description | None |
| `tests/agents/nazarick/test_agent_directory.py` | Python | No description | agents |
| `tests/agents/nazarick/test_chakra_resuscitator.py` | Python | Integration tests for :mod:`agents.nazarick.chakra_resuscitator`. | agents, citadel, monitoring, pytest, razar |
| `tests/agents/nazarick/test_doctrine_index.py` | Python | No description | agents |
| `tests/agents/nazarick/test_document_registry.py` | Python | Integration tests for the document registry. | agents, crown_router |
| `tests/agents/nazarick/test_ethics_manifesto.py` | Python | Tests for ethics manifesto. | agents |
| `tests/agents/nazarick/test_ethics_manifesto_integration.py` | Python | Integration tests for manifesto-based validation. | INANNA_AI, agents, crown_router, pytest |
| `tests/agents/nazarick/test_experience_replay.py` | Python | No description | agents |
| `tests/agents/nazarick/test_resuscitator_flow.py` | Python | Integration tests for :mod:`agents.nazarick.resuscitator`. | agents |
| `tests/agents/nazarick/test_task_orchestrator.py` | Python | Tests for :mod:`agents.task_orchestrator`. | agents, citadel |
| `tests/agents/nazarick/test_trust_matrix.py` | Python | Tests for trust matrix. | agents |
| `tests/agents/razar/conftest.py` | Python | Fixtures for RAZAR runtime tests. | agents, pytest, yaml |
| `tests/agents/razar/test_agent_heartbeat.py` | Python | No description | agents, monitoring, pytest |
| `tests/agents/razar/test_ai_invoker.py` | Python | Tests for ai invoker. | agents |
| `tests/agents/razar/test_boot_orchestrator.py` | Python | No description | razar |
| `tests/agents/razar/test_boot_orchestrator_logging.py` | Python | Tests for boot orchestrator logging. | agents, pytest, razar |
| `tests/agents/razar/test_boot_sequence.py` | Python | Tests for boot sequence. | pytest, razar |
| `tests/agents/razar/test_checkpoint_manager.py` | Python | Tests for checkpoint manager. | agents |
| `tests/agents/razar/test_code_repair.py` | Python | Tests for code repair. | agents |
| `tests/agents/razar/test_crown_handshake.py` | Python | Tests for crown handshake. | pytest, razar |
| `tests/agents/razar/test_crown_link.py` | Python | Tests for crown link. | agents, websockets |
| `tests/agents/razar/test_ignition_builder.py` | Python | Tests for ignition builder. | agents |
| `tests/agents/razar/test_ignition_sequence.py` | Python | Tests for ignition sequence. | agents, razar |
| `tests/agents/razar/test_lifecycle_bus.py` | Python | No description | agents |
| `tests/agents/razar/test_mission_brief_rotation.py` | Python | Tests for mission brief rotation. | razar |
| `tests/agents/razar/test_mission_logging.py` | Python | No description | agents |
| `tests/agents/razar/test_module_builder.py` | Python | Tests for module builder. | agents |
| `tests/agents/razar/test_planning_engine.py` | Python | Tests for planning engine. | agents, yaml |
| `tests/agents/razar/test_pytest_runner.py` | Python | Tests for pytest runner. | agents |
| `tests/agents/razar/test_quarantine_manager.py` | Python | Tests for quarantine manager. | agents |
| `tests/agents/razar/test_recovery_integration.py` | Python | Integration test for RecoveryManager and Nazarick ChakraResuscitator. | agents |
| `tests/agents/razar/test_runtime_manager.py` | Python | Tests for runtime manager. | agents, yaml |
| `tests/agents/razar/test_servant_launch.py` | Python | Tests for launch_servants.sh behavior. | yaml |
| `tests/agents/razar/test_state_validator.py` | Python | No description | agents |
| `tests/agents/razar/test_vision_adapter.py` | Python | Tests for vision adapter. | agents, numpy |
| `tests/agents/test_asian_gen.py` | Python | Tests for asian gen. | agents, pytest |
| `tests/agents/test_bana.py` | Python | Tests for bana. | agents, numpy, pytest |
| `tests/agents/test_bana_narrator.py` | Python | Tests for bana narrator. | agents, numpy |
| `tests/agents/test_event_bus.py` | Python | Tests for event bus. | agents, citadel |
| `tests/agents/test_land_graph_geo_knowledge.py` | Python | Tests for land graph geo knowledge. | agents |
| `tests/agents/test_narrative_scribe.py` | Python | Tests for narrative scribe. | agents, citadel, memory |
| `tests/agents/test_razar_blueprint_synthesizer.py` | Python | Tests for razar blueprint synthesizer. | None |
| `tests/agents/test_razar_cli.py` | Python | Tests for razar cli. | agents |
| `tests/agents/test_story_adapter.py` | Python | Tests for the narrative story adapter. | agents, memory |
| `tests/agents/test_vanna_data.py` | Python | Tests for vanna_data agent. | agents, pytest |
| `tests/audio/test_mix_tracks.py` | Python | Tests for mix tracks. | numpy, pytest, src |
| `tests/bana/test_event_structurizer.py` | Python | Tests for event structurizer. | bana, jsonschema, pytest |
| `tests/chakra_healing/__init__.py` | Python | Tests for chakra healing modules. | None |
| `tests/chakra_healing/common.py` | Python | Test helpers for chakra healing agents. | agents |
| `tests/chakra_healing/test_crown.py` | Python | Tests for crown chakra healing agent. | agents, tests |
| `tests/chakra_healing/test_heart.py` | Python | Tests for heart chakra healing agent. | agents, tests |
| `tests/chakra_healing/test_root.py` | Python | Tests for root chakra healing agent. | agents, tests |
| `tests/chakra_healing/test_sacral.py` | Python | Tests for sacral chakra healing agent. | agents, tests |
| `tests/chakra_healing/test_solar.py` | Python | Tests for solar chakra healing agent. | agents, tests |
| `tests/chakra_healing/test_third_eye.py` | Python | Tests for third eye chakra healing agent. | agents, tests |
| `tests/chakra_healing/test_throat.py` | Python | Tests for throat chakra healing agent. | agents, tests |
| `tests/chakracon/test_api.py` | Python | Tests for chakracon API endpoints. | chakracon, fastapi, pytest |
| `tests/communication/test_mcp_fallback.py` | Python | No description | None |
| `tests/communication/test_mcp_wrappers.py` | Python | No description | httpx, pytest, tests |
| `tests/conftest.py` | Python | Pytest configuration and shared fixtures. | coverage, prometheus_client, pytest, scipy, scripts, spiral_os |
| `tests/connectors/test_avatar_broadcast.py` | Python | No description | None |
| `tests/connectors/test_connector_heartbeat.py` | Python | No description | connectors |
| `tests/connectors/test_message_formatter.py` | Python | No description | None |
| `tests/connectors/test_signal_bus.py` | Python | No description | connectors |
| `tests/core/test_memory_physical.py` | Python | Tests for memory physical. | core, numpy, pytest |
| `tests/crown/server/test_openwebui_bridge.py` | Python | No description | httpx, pytest, tests |
| `tests/crown/server/test_server.py` | Python | Tests for server. | crown_config, fastapi, httpx, numpy |
| `tests/crown/test_config.py` | Python | Tests for crown config. | crown_config |
| `tests/crown/test_console_startup.py` | Python | Tests for crown console startup. | pytest |
| `tests/crown/test_console_streaming.py` | Python | Integration tests for console streaming and Bana log creation. | memory, pytest, tools |
| `tests/crown/test_decider.py` | Python | Tests for crown decider. | None |
| `tests/crown/test_decider_history.py` | Python | Tests for crown decider history. | None |
| `tests/crown/test_decider_rotation.py` | Python | Tests for crown decider rotation. | None |
| `tests/crown/test_glm_health_check.py` | Python | Tests for GLM health check during startup. | pytest |
| `tests/crown/test_initialization.py` | Python | Tests for crown initialization. | INANNA_AI, pytest |
| `tests/crown/test_orchestrator_music.py` | Python | Tests for orchestrator crown music. | numpy, rag |
| `tests/crown/test_prompt_orchestrator.py` | Python | Tests for crown prompt orchestrator. | INANNA_AI, pytest |
| `tests/crown/test_router_memory.py` | Python | Tests for crown router memory. | crown_router, pytest |
| `tests/crown/test_servant_registration.py` | Python | Tests for crown servant registration. | INANNA_AI, pytest, yaml |
| `tests/crown/test_servant_routing.py` | Python | No description | None |
| `tests/crown/test_start_console_py.py` | Python | Tests for start crown console py. | None |
| `tests/crown/test_start_console_trap.py` | Python | Tests for start crown console trap. | pytest |
| `tests/data/short_wav_base64.py` | Python | Tests for short wav base64. | None |
| `tests/data/test1_wav_base64.py` | Python | Tests for test1 wav base64. | None |
| `tests/docs/test_connector_links.py` | Python | No description | None |
| `tests/docs/test_doctrine_links.py` | Python | No description | None |
| `tests/docs/test_ui_links.py` | Python | No description | None |
| `tests/fixtures/razar_base_module.py` | Python | Tests for razar base module. | None |
| `tests/heart/memory_emotional/test_memory_emotional.py` | Python | Tests for memory emotional. | memory, pytest |
| `tests/helpers/config_stub.py` | Python | Provide a minimal configuration object for tests. | None |
| `tests/helpers/emotion_stub.py` | Python | Minimal stub for :mod:`INANNA_AI.emotion_analysis` used in tests. | None |
| `tests/helpers/mock_training_data.py` | Python | Tests for mock training data. | None |
| `tests/ignition/test_crown_wakes_services.py` | Python | Tests for crown wakes services. | agents, numpy, pytest, razar |
| `tests/ignition/test_full_stack.py` | Python | Tests for full stack. | agents, pytest, razar |
| `tests/ignition/test_validate_ignition_script.py` | Python | Tests for validate ignition script. | scripts |
| `tests/integration/test_context_rl.py` | Python | No description | memory, pytest |
| `tests/integration/test_core_regressions.py` | Python | No description | INANNA_AI_AGENT, pytest, rag, tests |
| `tests/integration/test_full_flows.py` | Python | No description | crown_query_router, rag, tests |
| `tests/integration/test_mix_and_store.py` | Python | Tests for mix and store. | core, numpy, src |
| `tests/memory/test_chakra_registry.py` | Python | No description | memory |
| `tests/memory/test_cortex_concurrency.py` | Python | Concurrency checks for cortex memory operations. | memory |
| `tests/memory/test_memory_store_fallback.py` | Python | Tests for memory store fallback. | None |
| `tests/memory/test_replication.py` | Python | Tests for distributed memory replication. | None |
| `tests/memory/test_sharded_memory_store.py` | Python | Tests for sharded memory store. | numpy |
| `tests/memory/test_vector_memory.py` | Python | Verify snapshot persistence and clustering for vector memory. | numpy, pytest |
| `tests/memory/test_vector_persistence.py` | Python | Exercise FAISS/SQLite backed vector persistence. | numpy, pytest |
| `tests/monitoring/test_avatar_watchdog.py` | Python | No description | agents, citadel, monitoring |
| `tests/monitoring/test_chakra_heartbeat.py` | Python | No description | agents, crown_router, monitoring, pytest |
| `tests/monitoring/test_chakra_status_board.py` | Python | No description | agents, fastapi, monitoring, pytest |
| `tests/monitoring/test_chakra_watchdog.py` | Python | No description | agents, citadel, monitoring |
| `tests/monitoring/test_escalation_notifier.py` | Python | No description | monitoring, pytest |
| `tests/monitoring/test_heartbeat_logger.py` | Python | No description | monitoring, pytest, scripts |
| `tests/monitoring/test_self_healing_ledger.py` | Python | No description | monitoring |
| `tests/narrative/test_narrative_api.py` | Python | No description | fastapi |
| `tests/narrative/test_self_heal_logging.py` | Python | Tests for self-heal narrative logging. | agents, citadel, memory |
| `tests/narrative/test_story_lookup.py` | Python | Verify joining of stories and events with filtering. | memory, pytest |
| `tests/narrative_engine/test_biosignal_pipeline.py` | Python | Tests for biosignal pipeline. | memory, pytest, src |
| `tests/narrative_engine/test_biosignal_schema.py` | Python | Ensure biosignal samples follow expected schema. | pytest |
| `tests/narrative_engine/test_biosignal_transformation.py` | Python | Validate biosignal action transformation during ingestion. | memory, pytest, scripts |
| `tests/narrative_engine/test_dataset_hashes.py` | Python | Verify biosignal dataset hashes. | data, pytest |
| `tests/narrative_engine/test_event_storage.py` | Python | Ensure biosignal rows transform, persist, and can be retrieved. | memory, pytest, scripts |
| `tests/narrative_engine/test_ingest_persist_retrieve.py` | Python | Tests for ingest persist retrieve. | fastapi, memory, scripts |
| `tests/narrative_engine/test_ingestion_to_mistral_output.py` | Python | Tests for ingestion to mistral output. | memory, pytest, scripts, src |
| `tests/narrative_engine/test_jsonl_ingest_persist_retrieve.py` | Python | Tests for jsonl ingest persist retrieve. | memory, scripts |
| `tests/narrative_engine/test_multitrack_output.py` | Python | Tests for multitrack output. | core, memory |
| `tests/nazarick/test_chakra_observer.py` | Python | No description | agents, citadel |
| `tests/performance/test_task_parser_performance.py` | Python | Tests for task parser performance. | None |
| `tests/performance/test_vector_memory_performance.py` | Python | Tests for vector memory performance. | None |
| `tests/razar/test_ai_invoker.py` | Python | Tests for razar.ai_invoker opencode integration. | agents, razar |
| `tests/razar/test_long_task.py` | Python | No description | pytest, razar |
| `tests/razar/test_remote_repair.py` | Python | Tests remote repair through the boot orchestrator. | agents, pytest, razar, tools |
| `tests/razar/test_retry_with_ai.py` | Python | Tests for retry logic with Opencode patch. | pytest, razar |
| `tests/root/test_chakra_integration.py` | Python | Tests for root chakra integration. | INANNA_AI, INANNA_AI_AGENT, dashboard |
| `tests/root/test_metrics_logging.py` | Python | Tests for root metrics logging. | None |
| `tests/scripts/test_audit_doctrine.py` | Python | No description | pytest, scripts |
| `tests/scripts/test_sign_release.py` | Python | No description | None |
| `tests/scripts/test_verify_chakra_monitoring.py` | Python | No description | pytest, scripts |
| `tests/scripts/test_verify_doctrine.py` | Python | No description | pytest, scripts |
| `tests/scripts/test_verify_doctrine_refs.py` | Python | No description | pytest, scripts |
| `tests/scripts/test_verify_self_healing.py` | Python | No description | pytest, scripts |
| `tests/spiral_os/test_chakra_cycle.py` | Python | Tests for chakra cycle persistence. | spiral_os |
| `tests/test_adaptive_learning.py` | Python | Tests for adaptive learning. | INANNA_AI, pytest |
| `tests/test_adaptive_learning_stub.py` | Python | Tests for adaptive learning stub. | None |
| `tests/test_albedo_layer.py` | Python | Tests for albedo layer. | INANNA_AI |
| `tests/test_albedo_personality.py` | Python | Tests for albedo personality. | INANNA_AI |
| `tests/test_albedo_state_machine.py` | Python | Tests for albedo state machine. | albedo |
| `tests/test_albedo_trust.py` | Python | Tests for albedo trust. | agents, albedo, src |
| `tests/test_alchemical_persona.py` | Python | Tests for alchemical persona. | INANNA_AI, numpy |
| `tests/test_api_endpoints.py` | Python | Tests for api endpoints. | fastapi |
| `tests/test_archetype_feedback_loop.py` | Python | Tests for archetype feedback loop. | memory |
| `tests/test_archetype_shift.py` | Python | Tests for archetype shift. | None |
| `tests/test_audio_backends.py` | Python | Tests for audio backends when soundfile is absent. | audio, numpy, pytest |
| `tests/test_audio_emotion_listener.py` | Python | Tests for audio emotion listener. | INANNA_AI, numpy |
| `tests/test_audio_engine.py` | Python | Tests for audio engine. | audio, pytest |
| `tests/test_audio_ingestion.py` | Python | Tests for audio ingestion. | audio, numpy, pytest |
| `tests/test_audio_segment.py` | Python | Tests for AudioSegment fallback to NpAudioSegment when soundfile is absent. | numpy |
| `tests/test_audio_tools.py` | Python | Tests for audio tools. | INANNA_AI, librosa, numpy, pytest, tests |
| `tests/test_audio_video_sync_profile.py` | Python | Tests for audio video sync profile. | numpy, pytest, src |
| `tests/test_auto_retrain.py` | Python | Tests for auto retrain. | pytest, tests |
| `tests/test_autoretrain_full.py` | Python | Tests for autoretrain full. | tests |
| `tests/test_avatar_console_startup.py` | Python | Tests for avatar console startup. | pytest |
| `tests/test_avatar_expression_engine.py` | Python | Tests for avatar expression engine. | audio, core, numpy |
| `tests/test_avatar_lipsync.py` | Python | Tests for avatar lipsync. | numpy, pytest |
| `tests/test_avatar_pipeline.py` | Python | Tests for avatar pipeline. | core, numpy |
| `tests/test_avatar_state_logging.py` | Python | Tests for avatar state logging. | pytest, rag |
| `tests/test_avatar_stream_pipeline.py` | Python | Tests for avatar stream pipeline. | INANNA_AI, audio, core, crown_config, fastapi, numpy, pytest, rag |
| `tests/test_avatar_voice.py` | Python | Tests for avatar voice. | audio, core, numpy |
| `tests/test_bana_narrative_engine.py` | Python | Tests for Bana narrative engine multitrack composition. | memory |
| `tests/test_benchmark.py` | Python | Tests for benchmark. | INANNA_AI_AGENT |
| `tests/test_boot_orchestrator.py` | Python | No description | razar |
| `tests/test_boot_sequence.py` | Python | No description | pytest, razar, scripts |
| `tests/test_bootstrap.py` | Python | Tests for the bootstrap script. | pytest, scripts |
| `tests/test_bots.py` | Python | Tests for bots. | pytest, tools |
| `tests/test_chat2db_integration.py` | Python | Integration test for Chat2DB combining SQLite and vector layers. | INANNA_AI, numpy |
| `tests/test_checklist_links.py` | Python | No description | None |
| `tests/test_citadel_event_processor.py` | Python | Tests for citadel event processor. | citadel |
| `tests/test_citadel_event_producer.py` | Python | Tests for citadel event producer. | citadel |
| `tests/test_citrinitas_cycle.py` | Python | Tests for citrinitas cycle. | None |
| `tests/test_citrinitas_layer.py` | Python | Tests for citrinitas layer. | INANNA_AI |
| `tests/test_citrinitas_ritual.py` | Python | Tests for citrinitas ritual. | core, pytest |
| `tests/test_config_model.py` | Python | Tests for the configuration model. | core |
| `tests/test_config_registry.py` | Python | No description | agents, memory, pytest, worlds |
| `tests/test_console_reflection.py` | Python | Tests for console reflection. | pytest |
| `tests/test_console_sandbox_command.py` | Python | Tests for /sandbox command in console interface. | None |
| `tests/test_core_scipy_smoke.py` | Python | Smoke test ensuring core package and SciPy are importable. | core, scipy |
| `tests/test_core_services.py` | Python | Tests for core services. | core, tests |
| `tests/test_corpus_logging.py` | Python | Tests for corpus logging. | None |
| `tests/test_corpus_memory.py` | Python | Tests for corpus memory. | INANNA_AI, numpy, pytest |
| `tests/test_corpus_memory_extended.py` | Python | Tests for corpus memory extended. | INANNA_AI |
| `tests/test_corpus_memory_logging.py` | Python | Tests for corpus memory logging. | None |
| `tests/test_cortex_memory.py` | Python | Tests for cortex memory. | memory |
| `tests/test_cortex_sigil_logic.py` | Python | Tests for cortex sigil logic. | labs |
| `tests/test_dashboard_app.py` | Python | Tests for dashboard app. | numpy, pandas, streamlit |
| `tests/test_dashboard_qnl_mixer.py` | Python | Tests for dashboard qnl mixer. | numpy, streamlit |
| `tests/test_dashboard_usage.py` | Python | Tests for dashboard usage. | None |
| `tests/test_data_pipeline.py` | Python | Tests for data pipeline. | None |
| `tests/test_defensive_network_utils.py` | Python | Tests for defensive network utils. | INANNA_AI, pytest |
| `tests/test_dependency_installer.py` | Python | Tests for tools.dependency_installer via sandbox_session. | pytest, tools |
| `tests/test_deployment_configs.py` | Python | Tests for deployment configs. | yaml |
| `tests/test_dev_orchestrator.py` | Python | Tests for dev orchestrator. | pytest, tools |
| `tests/test_download_deepseek.py` | Python | Tests for download deepseek. | pytest |
| `tests/test_download_model.py` | Python | Tests for the DeepSeek model downloader. | pytest |
| `tests/test_download_models.py` | Python | Tests for the model download utility. | pytest |
| `tests/test_dsp_engine.py` | Python | Tests for dsp engine. | audio, numpy, pytest |
| `tests/test_emotion_classifier.py` | Python | Tests for emotion classifier. | ml, numpy, tests |
| `tests/test_emotion_loop.py` | Python | Tests for emotion loop. | core, pytest |
| `tests/test_emotion_music_map.py` | Python | Tests for emotion music map. | MUSIC_FOUNDATION |
| `tests/test_emotion_registry.py` | Python | Tests for emotion registry. | pytest, yaml |
| `tests/test_emotion_state.py` | Python | Concurrency and persistence tests for emotional_state. | pytest |
| `tests/test_emotional_memory.py` | Python | Tests for emotional memory. | INANNA_AI |
| `tests/test_emotional_state.py` | Python | Tests for emotional state. | pytest |
| `tests/test_emotional_state_logging.py` | Python | Smoke test for emotion event logging. | pytest |
| `tests/test_emotional_synaptic_engine.py` | Python | Tests for emotional synaptic engine. | INANNA_AI |
| `tests/test_emotional_voice.py` | Python | Tests for emotional voice. | INANNA_AI |
| `tests/test_enlightened_prompt.py` | Python | Tests for enlightened prompt builder. | INANNA_AI, numpy |
| `tests/test_env_validation.py` | Python | Tests for env validation. | pytest |
| `tests/test_ethical_validator.py` | Python | Tests for ethical validator. | INANNA_AI, pytest |
| `tests/test_existential_reflector.py` | Python | Tests for existential reflector. | INANNA_AI, INANNA_AI_AGENT |
| `tests/test_expressive_output.py` | Python | Tests for expressive output. | core, numpy |
| `tests/test_feedback_logging.py` | Python | Tests for feedback logging. | INANNA_AI |
| `tests/test_feedback_logging_import.py` | Python | Regression tests for the feedback_logging compatibility wrapper. | pytest |
| `tests/test_full_audio_pipeline.py` | Python | Tests for full audio pipeline. | SPIRAL_OS, audio, numpy, pytest |
| `tests/test_gateway.py` | Python | Tests for gateway. | communication |
| `tests/test_github_metadata.py` | Python | Tests for github metadata. | INANNA_AI |
| `tests/test_github_scraper.py` | Python | Tests for github scraper. | INANNA_AI |
| `tests/test_github_scraper_enhanced.py` | Python | Tests for github scraper enhanced. | INANNA_AI |
| `tests/test_glm_command.py` | Python | Test the GLM command endpoint authorization and command filtering. | crown_config, httpx, pytest |
| `tests/test_glm_modules.py` | Python | Tests for glm modules. | INANNA_AI, pytest |
| `tests/test_glm_shell.py` | Python | Tests for glm shell. | INANNA_AI, pytest |
| `tests/test_hex_to_glyphs_smoke.py` | Python | Tests for hex to glyphs smoke. | SPIRAL_OS, numpy |
| `tests/test_inanna_ai.py` | Python | Tests for inanna ai. | INANNA_AI, INANNA_AI_AGENT, pytest |
| `tests/test_inanna_music_cli.py` | Python | Tests for inanna music cli. | tests |
| `tests/test_inanna_voice.py` | Python | Tests for inanna voice. | pytest |
| `tests/test_initial_listen.py` | Python | Tests for initial listen. | pytest |
| `tests/test_insight_compiler.py` | Python | Tests for insight compiler. | jsonschema |
| `tests/test_integrity.py` | Python | Tests for integrity. | INANNA_AI, OpenSSL, numpy, pytest |
| `tests/test_interactions_jsonl.py` | Python | Tests for logging sample interactions to JSONL. | None |
| `tests/test_interactions_jsonl_integrity.py` | Python | Additional JSONL integrity tests for interaction logging. | None |
| `tests/test_interconnectivity.py` | Python | Tests for interconnectivity. | core, rag |
| `tests/test_introspection_api.py` | Python | Tests for introspection api. | fastapi, pytest |
| `tests/test_invocation_engine.py` | Python | Tests for invocation engine. | None |
| `tests/test_kimi_k2_servant.py` | Python | Tests for kimi k2 servant. | INANNA_AI, yaml |
| `tests/test_kimi_servant.py` | Python | Tests for kimi servant. | tools |
| `tests/test_language_model_layer.py` | Python | Tests for language model layer. | None |
| `tests/test_launch_servants_script.py` | Python | Tests for launch servants script. | pytest |
| `tests/test_learning.py` | Python | Tests for learning. | INANNA_AI |
| `tests/test_learning_mutator.py` | Python | Tests for learning mutator. | pytest, tests |
| `tests/test_learning_mutator_personality.py` | Python | Tests for learning mutator personality. | None |
| `tests/test_lip_sync.py` | Python | Tests for lip sync. | ai_core |
| `tests/test_listening_engine.py` | Python | Tests for listening engine. | INANNA_AI, numpy |
| `tests/test_logging_config_rotation.py` | Python | Tests for logging config rotation. | yaml |
| `tests/test_logging_filters.py` | Python | Tests for logging filters. | None |
| `tests/test_lwm.py` | Python | Tests for LWM integration and inspection routes. | fastapi, pytest, src |
| `tests/test_lwm_config.py` | Python | Tests for the LWM configuration model. | lwm, pytest |
| `tests/test_media_audio.py` | Python | Regression tests for media.audio package. | pytest, src |
| `tests/test_media_avatar.py` | Python | Regression tests for media.avatar package. | pytest, src |
| `tests/test_media_video.py` | Python | Regression tests for media.video module. | pytest, src |
| `tests/test_memory_bundle.py` | Python | Tests for MemoryBundle layer initialization events. | agents, citadel, memory, pytest, tests |
| `tests/test_memory_bundle_tracing.py` | Python | No description | tests |
| `tests/test_memory_bus.py` | Python | Examples for memory bus and query aggregator. | agents, citadel, memory, pytest, scripts |
| `tests/test_memory_persistence.py` | Python | Test concurrent vector memory persistence and recovery. | fakeredis, pytest |
| `tests/test_memory_search.py` | Python | Tests for memory search. | memory |
| `tests/test_memory_snapshot.py` | Python | Tests for memory snapshot. | None |
| `tests/test_memory_spiritual.py` | Python | Tests for the spiritual memory ontology database. | memory |
| `tests/test_memory_store.py` | Python | Tests for memory store. | numpy |
| `tests/test_metrics_endpoints.py` | Python | No description | bana, crown_router, fastapi, memory, prometheus_fastapi_instrumentator |
| `tests/test_mission_logger.py` | Python | Tests for mission logger. | razar |
| `tests/test_mix_tracks.py` | Python | Tests for mix tracks. | audio, numpy, soundfile |
| `tests/test_mix_tracks_emotion.py` | Python | Tests for mix tracks emotion. | audio, numpy |
| `tests/test_mix_tracks_instructions.py` | Python | Tests for mix tracks instructions. | audio, numpy, soundfile |
| `tests/test_model.py` | Python | Tests for model. | pytest, tokenizers, transformers |
| `tests/test_model_benchmarking.py` | Python | Tests for model benchmarking. | INANNA_AI, core, rag, tests |
| `tests/test_modulation_arrangement.py` | Python | Tests for modulation arrangement. | pytest |
| `tests/test_music_analysis_pipeline.py` | Python | Tests for music analysis pipeline. | numpy |
| `tests/test_music_backends_missing.py` | Python | Tests for graceful backend fallbacks. | numpy, pytest |
| `tests/test_music_generation.py` | Python | Tests for music generation. | pytest |
| `tests/test_music_generation_emotion.py` | Python | Tests for music generation emotion. | pytest |
| `tests/test_music_generation_invocation.py` | Python | Tests for ritual invocation integration with music generation. | None |
| `tests/test_music_generation_missing_pipeline.py` | Python | Tests for missing transformers pipeline. | pytest |
| `tests/test_music_generation_streaming.py` | Python | Additional tests for music generation streaming and parameters. | pytest, src |
| `tests/test_music_llm_interface_prompt.py` | Python | Tests for generating music via prompt in music_llm_interface. | None |
| `tests/test_music_memory.py` | Python | Tests for music memory. | memory, numpy |
| `tests/test_nazarick_messaging.py` | Python | Tests for nazarick messaging. | agents, albedo |
| `tests/test_neoabzu_bindings.py` | Python | No description | pytest |
| `tests/test_network_schedule.py` | Python | Tests for network schedule. | INANNA_AI |
| `tests/test_network_utils.py` | Python | Tests for network utils. | INANNA_AI |
| `tests/test_nigredo_layer.py` | Python | Tests for nigredo layer. | INANNA_AI |
| `tests/test_numeric_cosine_similarity.py` | Python | Parity tests for numeric.cosine_similarity. | neoabzu_numeric |
| `tests/test_opencv_import.py` | Python | Ensure OpenCV can be imported and has a spec. | cv2 |
| `tests/test_openwebui_state_updates.py` | Python | Tests for openwebui state updates. | fastapi, httpx, tests |
| `tests/test_operator_api.py` | Python | Tests for operator api. | fastapi, pytest |
| `tests/test_operator_audit.py` | Python | Audit logging for operator commands. | fastapi, pytest |
| `tests/test_operator_command_route.py` | Python | Tests for operator command route. | fastapi, pytest |
| `tests/test_optional_imports.py` | Python | Tests for optional imports. | None |
| `tests/test_orchestration_master.py` | Python | Tests for orchestration master optional agents. | src |
| `tests/test_orchestrator.py` | Python | Tests for orchestrator. | core, rag, tests |
| `tests/test_orchestrator_handle.py` | Python | Tests for orchestrator handle. | pytest, rag |
| `tests/test_orchestrator_integration.py` | Python | Tests for orchestrator integration. | core, rag, tests |
| `tests/test_orchestrator_memory.py` | Python | Tests for orchestrator memory. | rag |
| `tests/test_orchestrator_routing.py` | Python | Tests for orchestrator routing. | crown_config, numpy, rag |
| `tests/test_orchestrator_suggestions_logging.py` | Python | Tests for orchestrator suggestions logging. | rag |
| `tests/test_os_guardian.py` | Python | Tests for os guardian. | None |
| `tests/test_os_guardian_action_engine.py` | Python | Tests for os guardian action engine. | None |
| `tests/test_os_guardian_perception.py` | Python | Tests for os guardian perception. | None |
| `tests/test_os_guardian_planning.py` | Python | Tests for os guardian planning. | None |
| `tests/test_personality_layers.py` | Python | Tests for personality layers. | INANNA_AI, pytest |
| `tests/test_phoneme_blendshape_alignment.py` | Python | Integration tests for phoneme extraction and blendshape mapping. | ai_core |
| `tests/test_pipeline_cli.py` | Python | Tests for pipeline cli. | None |
| `tests/test_play_ritual_music.py` | Python | Tests for play ritual music. | audio, numpy |
| `tests/test_play_ritual_music_smoke.py` | Python | Smoke test for ritual music playback. | audio, numpy, pytest |
| `tests/test_predictive_gate.py` | Python | Tests for predictive gate. | INANNA_AI |
| `tests/test_preprocess.py` | Python | Tests for preprocess. | INANNA_AI_AGENT, numpy, pytest |
| `tests/test_project_audit.py` | Python | Tests for project audit. | tools |
| `tests/test_project_gutenberg.py` | Python | Tests for project gutenberg. | INANNA_AI |
| `tests/test_prometheus_metrics.py` | Python | No description | fastapi, numpy, prometheus_client, prometheus_fastapi_instrumentator |
| `tests/test_prompt_engineering.py` | Python | Tests for prompt engineering. | None |
| `tests/test_qnl_audio_pipeline.py` | Python | Tests for qnl audio pipeline. | INANNA_AI_AGENT, audio, numpy, pytest |
| `tests/test_qnl_engine.py` | Python | Tests for qnl engine. | SPIRAL_OS, numpy |
| `tests/test_qnl_parser.py` | Python | Tests for qnl parser. | SPIRAL_OS |
| `tests/test_qnl_utils.py` | Python | Tests for qnl utils. | MUSIC_FOUNDATION, numpy |
| `tests/test_quarantine_manager.py` | Python | Tests for quarantine manager. | pytest, razar |
| `tests/test_rag_embedder.py` | Python | Tests for rag embedder. | rag |
| `tests/test_rag_engine.py` | Python | Tests for rag engine. | pytest |
| `tests/test_rag_music_integration.py` | Python | Tests for rag music integration. | SPIRAL_OS, rag |
| `tests/test_rag_music_oracle.py` | Python | Tests for rag music oracle. | rag, tests |
| `tests/test_rag_parser.py` | Python | Tests for rag parser. | rag |
| `tests/test_rag_retriever.py` | Python | Tests for rag retriever. | numpy, rag |
| `tests/test_razar_health_checks.py` | Python | Tests for razar health checks. | razar |
| `tests/test_recursive_emotion_router.py` | Python | Tests for recursive emotion router. | None |
| `tests/test_reflection_integration.py` | Python | Tests for reflection integration. | rag |
| `tests/test_reflection_thresholds_env.py` | Python | Tests for reflection thresholds env. | tools |
| `tests/test_remote_loader.py` | Python | Tests for remote loader. | None |
| `tests/test_response_manager.py` | Python | Tests for response manager. | INANNA_AI |
| `tests/test_retrain_and_deploy.py` | Python | Tests for retrain and deploy. | INANNA_AI |
| `tests/test_retrain_model.py` | Python | Tests for retrain model. | None |
| `tests/test_ritual_cli.py` | Python | Tests for ritual cli. | None |
| `tests/test_rival_messaging.py` | Python | Tests for rival messaging. | agents, albedo, src |
| `tests/test_rl_metrics.py` | Python | Tests for rl metrics. | INANNA_AI |
| `tests/test_rubedo_layer.py` | Python | Tests for rubedo layer. | INANNA_AI |
| `tests/test_run_inanna_sh.py` | Python | Tests for run inanna sh. | pytest |
| `tests/test_run_song_demo.py` | Python | Tests for run song demo. | tests |
| `tests/test_sandbox_session.py` | Python | Tests for tools.sandbox_session. | tools |
| `tests/test_schema_validation.py` | Python | Tests for schema validation. | jsonschema |
| `tests/test_security_canary.py` | Python | Tests for security canary. | agents |
| `tests/test_self_correction_engine.py` | Python | Tests for self correction engine. | core |
| `tests/test_servant_download.py` | Python | Verify servant model registration via download CLI. | pytest |
| `tests/test_servant_model_manager.py` | Python | Tests for servant model manager. | None |
| `tests/test_server_endpoints.py` | Python | Exercise lightweight server endpoints. | crown_config, fastapi, pytest |
| `tests/test_session_logger.py` | Python | Tests for session logger. | tools |
| `tests/test_seven_dimensional_music.py` | Python | Tests for seven dimensional music. | MUSIC_FOUNDATION, SPIRAL_OS, numpy, soundfile |
| `tests/test_seven_plane_analyzer.py` | Python | Tests for seven plane analyzer. | MUSIC_FOUNDATION, numpy, soundfile |
| `tests/test_silence_reflection.py` | Python | Tests for silence reflection. | INANNA_AI, numpy |
| `tests/test_silence_ritual.py` | Python | Tests for silence ritual. | rag |
| `tests/test_smoke_imports.py` | Python | Tests for smoke imports. | agents, src |
| `tests/test_sonic_emotion_mapper.py` | Python | Tests for sonic emotion mapper. | INANNA_AI |
| `tests/test_soul_ritual.py` | Python | Tests for soul ritual. | INANNA_AI, pytest, tests |
| `tests/test_soul_state_manager.py` | Python | Tests for soul state manager. | None |
| `tests/test_source_loader.py` | Python | Tests for source loader. | INANNA_AI_AGENT |
| `tests/test_speaking_behavior.py` | Python | Tests for speaking behavior. | INANNA_AI |
| `tests/test_speaking_engine.py` | Python | Tests for speaking engine. | INANNA_AI, numpy |
| `tests/test_speaking_engine_streaming.py` | Python | Tests for speaking engine streaming. | INANNA_AI, numpy |
| `tests/test_speech_loopback_reflector.py` | Python | Tests for speech loopback reflector. | INANNA_AI |
| `tests/test_spiral_cortex_integration.py` | Python | Tests for spiral cortex integration. | memory |
| `tests/test_spiral_cortex_memory.py` | Python | Tests for spiral cortex memory. | memory, rag, tests |
| `tests/test_spiral_memory.py` | Python | Tests for spiral memory. | None |
| `tests/test_spiral_os.py` | Python | Tests for the spiral_os CLI pipeline utility. | pytest, yaml |
| `tests/test_spiral_vector_db.py` | Python | Tests for spiral vector db. | numpy |
| `tests/test_start_avatar_console.py` | Python | Tests for start avatar console. | pytest |
| `tests/test_start_dev_agents_triage.py` | Python | Tests for start dev agents triage. | None |
| `tests/test_start_spiral_os.py` | Python | Tests for start spiral os. | pytest, tests |
| `tests/test_state_transition_engine.py` | Python | Tests for state transition engine. | None |
| `tests/test_style_selection.py` | Python | Tests for style selection. | ai_core, style_engine |
| `tests/test_suggest_enhancement.py` | Python | Tests for suggest enhancement. | INANNA_AI_AGENT |
| `tests/test_symbolic_parser.py` | Python | Tests for symbolic parser. | SPIRAL_OS |
| `tests/test_synthetic_stego.py` | Python | Tests for synthetic stego. | MUSIC_FOUNDATION, numpy, soundfile |
| `tests/test_synthetic_stego_engine.py` | Python | Tests for synthetic stego engine. | MUSIC_FOUNDATION, numpy |
| `tests/test_system_monitor.py` | Python | Tests for system monitor. | dashboard |
| `tests/test_task_parser.py` | Python | Tests for task parser. | None |
| `tests/test_task_profiling.py` | Python | Tests for task profiling. | core |
| `tests/test_task_profiling_wrappers.py` | Python | Tests for task profiling wrappers. | core |
| `tests/test_tools_smoke.py` | Python | Tests for tools smoke. | numpy, tools |
| `tests/test_training_feedback.py` | Python | Tests for training feedback. | tests |
| `tests/test_training_guide.py` | Python | Tests for training guide. | INANNA_AI |
| `tests/test_training_guide_logger.py` | Python | Tests for training guide logger. | tests |
| `tests/test_training_guide_parser.py` | Python | Tests for training guide parser. | INANNA_AI |
| `tests/test_training_guide_trigger.py` | Python | Tests for training guide trigger. | tests |
| `tests/test_transformation_smoke.py` | Python | Smoke tests for transformation engines. | None |
| `tests/test_transformers_generate.py` | Python | Tests for huggingface-backed generation. | cv2, pytest, torch, transformers |
| `tests/test_trust_registry.py` | Python | Tests for trust registry. | memory |
| `tests/test_tts_backends.py` | Python | Tests for tts backends. | INANNA_AI, crown_config |
| `tests/test_utils_verify_insight_matrix.py` | Python | Tests for utils verify insight matrix. | INANNA_AI, pytest |
| `tests/test_vast_check.py` | Python | Tests for vast check. | aiortc, fastapi, httpx |
| `tests/test_vast_pipeline.py` | Python | Tests for vast pipeline. | SPIRAL_OS, aiortc, connectors, core, crown_config, fastapi, httpx, numpy, rag |
| `tests/test_vector_memory.py` | Python | Tests for vector memory. | numpy, pytest |
| `tests/test_vector_memory_extensions.py` | Python | Integration tests for extended vector memory features. | numpy, pytest, src |
| `tests/test_vector_memory_persistence.py` | Python | Tests for vector memory persistence. | None |
| `tests/test_video.py` | Python | Tests for video. | core, numpy, pytest |
| `tests/test_video_stream.py` | Python | Tests for the WebRTC video and audio streaming endpoints. | aiortc, crown_config, fastapi, httpx, numpy, pytest |
| `tests/test_video_stream_audio.py` | Python | Tests for video stream audio. | aiortc, crown_config, fastapi, httpx, numpy, pytest, soundfile |
| `tests/test_video_stream_helpers.py` | Python | Tests for video stream helper utilities. | numpy, pytest |
| `tests/test_virtual_env_manager.py` | Python | Tests for tools.virtual_env_manager. | tools |
| `tests/test_vocal_isolation.py` | Python | Tests for vocal isolation. | None |
| `tests/test_voice_aura.py` | Python | Tests for voice aura. | audio, numpy, pytest |
| `tests/test_voice_avatar_pipeline.py` | Python | Tests for voice avatar pipeline. | INANNA_AI, INANNA_AI_AGENT, core, crown_config, numpy, tools |
| `tests/test_voice_cloner_cli.py` | Python | Tests for voice cloning CLI and API using stubbed dependencies. | fastapi, numpy, src |
| `tests/test_voice_config.py` | Python | Tests for voice config. | INANNA_AI |
| `tests/test_voice_conversion.py` | Python | Tests for voice conversion. | INANNA_AI, crown_config, tools |
| `tests/test_voice_evolution.py` | Python | Tests for voice evolution. | INANNA_AI, numpy |
| `tests/test_voice_evolution_memory.py` | Python | Tests for voice evolution memory. | INANNA_AI |
| `tests/test_voice_layer_albedo.py` | Python | Tests for voice layer albedo. | INANNA_AI |
| `tests/test_voice_profiles.py` | Python | Tests for voice profiles. | INANNA_AI |
| `tests/test_webrtc_connector.py` | Python | Tests for webrtc connector. | aiortc, connectors, crown_config, fastapi, httpx, tests |
| `tests/tools/test_bot_mcp.py` | Python | Tests for MCP usage in bot connectors. | None |
| `tests/tools/test_opencode_client.py` | Python | Tests for ``tools.opencode_client``. | pytest, tools |
| `tests/vision/test_yoloe_adapter.py` | Python | Tests for yoloe adapter. | numpy, src |
| `tests/web_console/__init__.py` | Python | No description | None |
| `tests/web_console/test_agent_status_panel.py` | Python | No description | None |
| `tests/web_console/test_arcade_ui.py` | Python | No description | bs4 |
| `tests/web_console/test_chakra_pulse_panel.py` | Python | No description | None |
| `tests/web_console/test_chakra_status_panel.py` | Python | No description | None |
| `tests/web_console/test_connector_panel.py` | Python | No description | None |
| `tests/web_console/test_conversation_timeline.py` | Python | No description | fastapi, pytest |
| `tests/web_console/test_memory_panel.py` | Python | No description | None |
| `tests/web_console/test_multi_avatar_stream.py` | Python | Tests for simultaneous avatar sessions and heartbeat emission. | agents, citadel |
| `tests/web_console/test_self_healing_panel.py` | Python | No description | None |
| `tests/web_console/test_webrtc_gateway.py` | Python | Integration tests for the unified WebRTC gateway. | aiortc, fastapi |
| `tests/web_operator/__init__.py` | Python | No description | None |
| `tests/web_operator/test_api.py` | Python | Tests for operator_service.api. | fastapi, operator_service, pytest, razar |
| `tests/web_operator/test_arcade_flow.py` | Python | Arcade flow tests for web operator. | fastapi, operator_service, pytest, razar, scripts |
| `tests/web_operator/test_arcade_ui.py` | Python | Integration tests for operator arcade UI. | bs4, fastapi, operator_service |
| `tests/web_operator/test_ignition_e2e.py` | Python | End-to-end tests for operator_service ignition route. | fastapi, operator_service, pytest, razar |
| `tests/web_ui/test_boot_page.py` | Python | No description | fastapi |
| `tests/web_ui/test_memory_query.py` | Python | No description | fastapi |
| `tools/__init__.py` | Python | Developer tooling utilities. | None |
| `tools/bot_discord.py` | Python | Discord bot that forwards messages and emits heartbeats. | connectors, core, discord, requests |
| `tools/bot_telegram.py` | Python | Telegram bot forwarding messages and emitting heartbeats. | connectors, core, requests |
| `tools/component_fields_updater.py` | Python | Validate and update component index entries with required fields. | None |
| `tools/dependency_audit.py` | Python | Audit installed packages against pinned versions in ``pyproject.toml``. | tomli |
| `tools/dependency_installer.py` | Python | Install Python packages into a given virtual environment. | None |
| `tools/dev_orchestrator.py` | Python | Development cycle orchestrator using lightweight multi-agent workflow. | INANNA_AI, autogen |
| `tools/doc_indexer.py` | Python | Generate an index of Markdown documentation files. | None |
| `tools/kimi_k2_client.py` | Python | HTTP client for the Kimi-K2 servant model. | requests |
| `tools/opencode_client.py` | Python | Client for interacting with the Opencode servant model. | requests |
| `tools/preflight.py` | Python | Run basic environment validation in a single command. | None |
| `tools/project_audit.py` | Python | Simple project audit for Spiral OS. | None |
| `tools/reflection_loop.py` | Python | Mirror reflection loop utilities. | INANNA_AI, core, cv2, numpy |
| `tools/sandbox_session.py` | Python | Helpers for working with sandboxed repository copies. | None |
| `tools/session_logger.py` | Python | Utility functions to log session audio and video. | imageio, numpy |
| `tools/virtual_env_manager.py` | Python | Utilities for working with Python virtual environments. | None |
| `tools/voice_conversion.py` | Python | Command line wrappers for voice conversion tools. | None |
| `training/fine_tune_mistral.py` | Python | Fine-tune Mistral model on mythological and project corpora. | None |
| `training_guide.py` | Python | Log intent outcomes for reinforcement learning. | INANNA_AI, crown_config |
| `transformers/__init__.py` | Python | Thin wrapper around the real Hugging Face `transformers` package. | None |
| `ui_service.py` | Python | Lightweight UI service exposing memory and status endpoints. | fastapi, memory, prometheus_fastapi_instrumentator |
| `vector_memory.py` | Python | FAISS/SQLite-backed text vector store with decay and operation logging. | MUSIC_FOUNDATION, crown_config, faiss, memory, numpy, opentelemetry, sklearn |
| `video_stream.py` | Python | Compatibility wrapper for :mod:`video_stream` package. | None |
| `video_stream/__init__.py` | Python | WebRTC video/audio stream management with per-agent sessions. | communication |
| `video_stream/session_manager.py` | Python | Session manager for avatar tracks with heartbeat emission. | agents, communication |
| `vision/__init__.py` | Python | Vision utilities and adapters. | None |
| `vision/yoloe_adapter.py` | Python | YOLOE wrapper emitting detections to the LargeWorldModel. | numpy, ultralytics |
| `vocal_isolation.py` | Python | Helpers for isolating vocals and other stems using external tools. | src |
| `worlds/__init__.py` | Python | World configuration utilities. | None |
| `worlds/__main__.py` | Python | CLI utilities for exporting and importing world configuration. | None |
| `worlds/config_registry.py` | Python | Central registry for per-world configuration metadata. | None |
| `worlds/services.py` | Python | Service manifest loader for per-world settings. | yaml |
