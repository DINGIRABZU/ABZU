# Component Index

Generated automatically. Lists each Python file with its description and external dependencies.

| File | Description | Dependencies |
| --- | --- | --- |
| `INANNA_AI/__init__.py` | Core package for the INANNA AI helpers. | None |
| `INANNA_AI/adaptive_learning.py` | No description | core |
| `INANNA_AI/audio_emotion_listener.py` | No description | librosa, numpy, sounddevice |
| `INANNA_AI/context.py` | No description | None |
| `INANNA_AI/corpus_memory.py` | No description | chromadb, crown_config, numpy, sentence_transformers |
| `INANNA_AI/db_storage.py` | SQLite helpers to store voice interactions. | None |
| `INANNA_AI/defensive_network_utils.py` | Defensive network helpers for monitoring and secure POST requests. | requests, scapy |
| `INANNA_AI/emotion_analysis.py` | No description | librosa, numpy, opensmile, torch, transformers |
| `INANNA_AI/emotional_memory.py` | No description | None |
| `INANNA_AI/emotional_synaptic_engine.py` | No description | None |
| `INANNA_AI/ethical_validator.py` | Validate user prompts before hitting the language model. | numpy, sentence_transformers |
| `INANNA_AI/existential_reflector.py` | Generate a short self-description using a placeholder GLM endpoint. | requests |
| `INANNA_AI/gate_orchestrator.py` | Simple gate orchestrator translating text to/from complex vectors. | core, numpy, torch |
| `INANNA_AI/gates.py` | Signature helpers for the RFA core. | cryptography |
| `INANNA_AI/glm_analyze.py` | Analyze Python modules using a placeholder GLM endpoint. | INANNA_AI, requests |
| `INANNA_AI/glm_init.py` | Summarize project purpose using a placeholder GLM endpoint. | INANNA_AI, requests |
| `INANNA_AI/glm_integration.py` | No description | requests |
| `INANNA_AI/learning/__init__.py` | Utilities for fetching external learning data. | None |
| `INANNA_AI/learning/github_metadata.py` | No description | crown_config, requests |
| `INANNA_AI/learning/github_scraper.py` | No description | crown_config, requests, sentence_transformers |
| `INANNA_AI/learning/project_gutenberg.py` | No description | bs4, crown_config, requests, sentence_transformers |
| `INANNA_AI/learning/training_guide.py` | No description | None |
| `INANNA_AI/listening_engine.py` | No description | core, numpy |
| `INANNA_AI/love_matrix.py` | No description | None |
| `INANNA_AI/main.py` | No description | learning, numpy, personality_layers, rag |
| `INANNA_AI/network_utils/__init__.py` | Network monitoring utilities. | None |
| `INANNA_AI/network_utils/__main__.py` | Command line entry for network utilities. | None |
| `INANNA_AI/network_utils/analysis.py` | Basic traffic analysis for PCAP files. | scapy |
| `INANNA_AI/network_utils/capture.py` | Packet capture helpers using scapy or pyshark. | scapy |
| `INANNA_AI/network_utils/config.py` | Configuration helpers for network utilities. | None |
| `INANNA_AI/personality_layers/__init__.py` | Personality layers for INANNA AI. | albedo |
| `INANNA_AI/personality_layers/albedo/__init__.py` | No description | SPIRAL_OS |
| `INANNA_AI/personality_layers/albedo/alchemical_persona.py` | No description | MUSIC_FOUNDATION, numpy |
| `INANNA_AI/personality_layers/albedo/enlightened_prompt.py` | No description | None |
| `INANNA_AI/personality_layers/albedo/glm_integration.py` | No description | None |
| `INANNA_AI/personality_layers/albedo/state_contexts.py` | No description | None |
| `INANNA_AI/personality_layers/citrinitas_layer.py` | No description | None |
| `INANNA_AI/personality_layers/nigredo_layer.py` | No description | None |
| `INANNA_AI/personality_layers/rubedo_layer.py` | No description | None |
| `INANNA_AI/response_manager.py` | No description | None |
| `INANNA_AI/retrain_and_deploy.py` | No description | crown_config, mlflow |
| `INANNA_AI/rfa_7d.py` | Random Field Array 7D with quantum-like execution and DNA serialization. | numpy, qutip |
| `INANNA_AI/silence_reflection.py` | Detect sustained silence and suggest a short meaning. | numpy |
| `INANNA_AI/sonic_emotion_mapper.py` | No description | yaml |
| `INANNA_AI/speaking_engine.py` | Generate speech using gTTS with emotion-based style adjustments. | core, crown_config, numpy, tools |
| `INANNA_AI/speech_loopback_reflector.py` | No description | None |
| `INANNA_AI/stt_whisper.py` | Speech-to-text helpers using the Whisper library. | crown_config, whisper |
| `INANNA_AI/train_soul.py` | No description | core, numpy |
| `INANNA_AI/tts_bark.py` | No description | bark, numpy |
| `INANNA_AI/tts_coqui.py` | Text-to-speech helpers using the Coqui TTS library. | TTS, numpy |
| `INANNA_AI/tts_tortoise.py` | No description | numpy, tortoise |
| `INANNA_AI/tts_xtts.py` | No description | TTS, numpy |
| `INANNA_AI/utils.py` | Utility helpers for audio processing and logging. | core, numpy |
| `INANNA_AI/voice_evolution.py` | Helpers to evolve INANNA's vocal style. | crown_config, numpy, yaml |
| `INANNA_AI/voice_layer_albedo.py` | No description | None |
| `INANNA_AI_AGENT/__init__.py` | Convenience imports and CLI exposure for the INANNA AI agent. | None |
| `INANNA_AI_AGENT/benchmark_preprocess.py` | Benchmark preprocessing of INANNA AI source texts. | None |
| `INANNA_AI_AGENT/inanna_ai.py` | Command line interface for the INANNA AI system. | INANNA_AI, SPIRAL_OS, yaml |
| `INANNA_AI_AGENT/model.py` | Load local language models and tokenizers. | transformers |
| `INANNA_AI_AGENT/preprocess.py` | Text preprocessing utilities for INANNA AI rituals. | markdown, numpy, sentence_transformers |
| `INANNA_AI_AGENT/source_loader.py` | Utilities for reading ritual source texts. | None |
| `MUSIC_FOUNDATION/__init__.py` | Utilities and helpers for the Music Foundation package. | None |
| `MUSIC_FOUNDATION/human_music_to_qnl_converter.py` | No description | numpy |
| `MUSIC_FOUNDATION/inanna_music_COMPOSER_ai.py` | inanna_music_COMPOSER_ai.py | MUSIC_FOUNDATION, librosa, numpy, soundfile, yaml |
| `MUSIC_FOUNDATION/layer_generators.py` | Basic waveform generators for Spiral OS music layers. | librosa, numpy, soundfile |
| `MUSIC_FOUNDATION/music_foundation.py` | No description | librosa, numpy, soundfile |
| `MUSIC_FOUNDATION/qnl_utils.py` | No description | numpy, sentence_transformers |
| `MUSIC_FOUNDATION/seven_plane_analyzer.py` | Analyze audio features across seven metaphysical planes. | essentia, librosa, numpy |
| `MUSIC_FOUNDATION/synthetic_stego.py` | Simple LSB audio steganography utilities. | numpy, soundfile |
| `MUSIC_FOUNDATION/synthetic_stego_engine.py` | No description | numpy |
| `SPIRAL_OS/__init__.py` | Expose Spiral OS components and dynamic helpers. | None |
| `SPIRAL_OS/qnl_engine.py` | Utilities for converting hexadecimal input into QNL phrases and waveforms. | numpy |
| `SPIRAL_OS/symbolic_parser.py` | Intent parser that maps symbolic input to Spiral OS actions. | INANNA_AI |
| `agents/__init__.py` | Core agent packages for ABZU. | None |
| `agents/albedo/__init__.py` | Albedo agent messaging utilities and vision hooks. | agents |
| `agents/albedo/messaging.py` | No description | albedo, yaml |
| `agents/albedo/trust.py` | No description | agents, albedo, memory |
| `agents/albedo/vision.py` | No description | agents |
| `agents/asian_gen/__init__.py` | Asian language creative agents. | agents |
| `agents/asian_gen/creative_engine.py` | Creative engine for Asian language text generation. | sentencepiece, transformers |
| `agents/bana/__init__.py` | Bana bio-adaptive narrator agent. | agents |
| `agents/bana/bio_adaptive_narrator.py` | No description | biosppy, memory, numpy, transformers |
| `agents/cocytus/__init__.py` | Cocytus agent modules. | agents |
| `agents/cocytus/prompt_arbiter.py` | Cocytus prompt arbitration utilities. | None |
| `agents/demiurge/__init__.py` | Demiurge agent modules. | agents |
| `agents/demiurge/strategic_simulator.py` | Responsibilities: | None |
| `agents/ecosystem/__init__.py` | Ecosystem monitoring agents. | None |
| `agents/ecosystem/aura_capture.py` | Responsibilities: | None |
| `agents/ecosystem/mare_gardener.py` | Responsibilities: | None |
| `agents/event_bus.py` | No description | citadel |
| `agents/guardian.py` | Shared utilities for guardian agents. | cocytus |
| `agents/land_graph/__init__.py` | Land graph utilities. | None |
| `agents/land_graph/geo_knowledge.py` | Geo-referenced land graph utilities. | geopandas, networkx, shapely |
| `agents/nazarick/__init__.py` | No description | None |
| `agents/nazarick/ethics_manifesto.py` | No description | None |
| `agents/nazarick/narrative_scribe.py` | No description | aiokafka, citadel, memory, redis, yaml |
| `agents/nazarick/trust_matrix.py` | No description | None |
| `agents/operator_dispatcher.py` | No description | None |
| `agents/pandora/__init__.py` | Pandora persona agents. | agents |
| `agents/pandora/persona_emulator.py` | Responsibilities: | None |
| `agents/pleiades/__init__.py` | Pleiades utility modules. | agents |
| `agents/pleiades/signal_router.py` | Responsibilities: | None |
| `agents/pleiades/star_map.py` | Responsibilities: | None |
| `agents/razar/__init__.py` | RAZAR agents. | agents |
| `agents/razar/ai_invoker.py` | High level wrapper for remote RAZAR agents. | None |
| `agents/razar/blueprint_synthesizer.py` | No description | networkx |
| `agents/razar/boot_orchestrator.py` | Boot orchestrator for the RAZAR agent. | razar, yaml |
| `agents/razar/checkpoint_manager.py` | No description | None |
| `agents/razar/cli.py` | Command line utilities for RAZAR agents. | agents, memory |
| `agents/razar/code_repair.py` | Automated module repair using LLM patch suggestions. | INANNA_AI |
| `agents/razar/crown_link.py` | No description | websockets |
| `agents/razar/doc_sync.py` | No description | razar |
| `agents/razar/health_checks.py` | Health check routines for RAZAR runtime components. | prometheus_client |
| `agents/razar/ignition_builder.py` | Update ``docs/Ignition.md`` from the component priority registry. | yaml |
| `agents/razar/lifecycle_bus.py` | No description | redis |
| `agents/razar/mission_logger.py` | No description | None |
| `agents/razar/module_builder.py` | Utilities for constructing new RAZAR modules. | None |
| `agents/razar/planning_engine.py` | No description | networkx, yaml |
| `agents/razar/pytest_runner.py` | Prioritized pytest runner for RAZAR. | pytest, yaml |
| `agents/razar/quarantine_manager.py` | No description | agents |
| `agents/razar/recovery_manager.py` | No description | zmq |
| `agents/razar/remote_loader.py` | Download and load remote RAZAR agents at runtime. | git, requests |
| `agents/razar/retro_bootstrap.py` | No description | None |
| `agents/razar/runtime_manager.py` | RAZAR runtime manager. | yaml |
| `agents/razar/vision_adapter.py` | No description | agents |
| `agents/sebas/__init__.py` | Sebas compassion agents. | agents |
| `agents/sebas/compassion_module.py` | Responsibilities: | None |
| `agents/shalltear/__init__.py` | Shalltear agent modules. | agents |
| `agents/shalltear/fast_inference_agent.py` | Responsibilities: | None |
| `agents/vanna_data.py` | No description | agents, core, memory |
| `agents/victim/__init__.py` | Victim security agents. | agents |
| `agents/victim/security_canary.py` | Security canary for intrusion monitoring. | None |
| `ai_core/__init__.py` | Package initialization. | None |
| `ai_core/avatar/__init__.py` | Avatar animation utilities. | None |
| `ai_core/avatar/expression_controller.py` | No description | None |
| `ai_core/avatar/lip_sync.py` | No description | None |
| `ai_core/avatar/ltx_avatar.py` | No description | numpy |
| `ai_core/avatar/phonemes.py` | Phoneme extraction utilities. | phonemizer |
| `ai_core/video_pipeline/__init__.py` | Video processing pipeline components. | None |
| `ai_core/video_pipeline/ltx_video_processor.py` | No description | None |
| `ai_core/video_pipeline/pipeline.py` | Video generation pipeline that selects processors based on a ``StyleConfig``. | style_engine |
| `ai_core/video_pipeline/pusa_v1_processor.py` | No description | None |
| `albedo/__init__.py` | No description | None |
| `albedo/state_machine.py` | No description | None |
| `archetype_feedback_loop.py` | No description | memory |
| `archetype_shift_engine.py` | Determine when to switch personality layers based on ritual cues or emotion. | None |
| `aspect_processor.py` | No description | None |
| `auto_retrain.py` | Automatically trigger fine-tuning based on feedback metrics. | INANNA_AI, core, llm_api, mlflow, yaml |
| `benchmarks/chat_gateway_benchmark.py` | No description | communication |
| `benchmarks/llm_throughput_benchmark.py` | No description | torch |
| `benchmarks/memory_store_benchmark.py` | No description | None |
| `benchmarks/run_benchmarks.py` | No description | None |
| `benchmarks/train_infer.py` | Benchmark a minimal training and inference step. | torch |
| `citadel/__init__.py` | Event infrastructure for agents. | None |
| `citadel/event_processor.py` | No description | aiokafka, asyncpg, fastapi, neo4j, redis |
| `citadel/event_producer.py` | No description | aiokafka, redis |
| `communication/__init__.py` | Package initialization. | None |
| `communication/floor_channel_socket.py` | No description | socketio |
| `communication/gateway.py` | No description | api |
| `communication/telegram_bot.py` | Telegram bot forwarding messages to the avatar. | telegram |
| `communication/webrtc_server.py` | WebRTC signaling helpers and media tracks. | aiortc, core, mediasoup, numpy, soundfile |
| `connectors/__init__.py` | No description | None |
| `connectors/webrtc_connector.py` | WebRTC connector for streaming data, audio, and video. | aiortc, communication, fastapi |
| `corpus_memory_logging.py` | Append and read JSONL interaction records for corpus memory usage. | None |
| `crown_config/__init__.py` | Load application configuration from environment variables. | pydantic, pydantic_settings |
| `crown_config/settings/__init__.py` | Utilities for reading optional layer configuration. | yaml |
| `crown_decider.py` | Heuristics for selecting a language model in the Crown agent. | INANNA_AI, audio, crown_config |
| `crown_prompt_orchestrator.py` | Lightweight prompt orchestrator for the Crown console. | INANNA_AI, core, memory |
| `crown_query_router.py` | Route questions to archetype-specific vector stores. | rag |
| `crown_router.py` | Coordinate model and expression routing for the Crown agent. | rag |
| `deployment/__init__.py` | Package initialization. | None |
| `distributed_memory.py` | Redis-backed helper for off-box vector memory backups. | redis |
| `docs/onboarding/wizard.py` | Interactive quick-start wizard for ABZU. | None |
| `download_model.py` | Download DeepSeek-R1 weights from Hugging Face. | dotenv, huggingface_hub |
| `download_models.py` | CLI utilities for downloading model weights and dependencies. | dotenv, huggingface_hub, requests, transformers |
| `emotion_registry.py` | Persist emotional state and expose retrieval helpers. | None |
| `emotional_state.py` | Manage emotional and soul state persistence. | cryptography |
| `env_validation.py` | No description | None |
| `examples/ritual_demo.py` | Minimal emotion→music→insight demonstration. | audio, memory, simpleaudio |
| `examples/vision_wall_demo.py` | Minimal 2D→3D vision pipeline demonstration. | imageio, numpy, src |
| `glm_shell.py` | No description | INANNA_AI, crown_config |
| `init_crown_agent.py` | Initialize the crown agent and optional vector memory subsystem. | INANNA_AI, requests, yaml |
| `insight_compiler.py` | No description | jsonschema, requests |
| `introspection_api.py` | FastAPI service exposing an endpoint to return the AST of a module. | fastapi, prometheus_fastapi_instrumentator, pydantic, src |
| `invocation_engine.py` | Pattern-based invocation engine. | prometheus_client, rag |
| `labs/__init__.py` | Experimental modules and demonstrations. | None |
| `labs/cortex_sigil.py` | No description | None |
| `language_model_layer.py` | No description | None |
| `learning_mutator.py` | Suggest mutations to the intent matrix based on insight metrics. | None |
| `logging_filters.py` | Enrich log records with emotional context. | None |
| `memory/__init__.py` | Memory subsystem package. | None |
| `memory/cortex.py` | No description | None |
| `memory/cortex_cli.py` | Command line utilities for managing spiral memory. | None |
| `memory/emotional.py` | Persist and query emotional feature vectors in SQLite. | dlib, transformers |
| `memory/mental.py` | No description | core, crown_config |
| `memory/music_memory.py` | No description | numpy |
| `memory/narrative_engine.py` | Stub narrative memory engine. | None |
| `memory/sacred.py` | No description | PIL, torch |
| `memory/search.py` | Unified memory search across multiple subsystems. | memory |
| `memory/spiral_cortex.py` | No description | None |
| `memory/spiritual.py` | SQLite-backed event ↔ symbol memory. | None |
| `memory/trust_registry.py` | No description | None |
| `memory_scribe.py` | Stub for the Memory Scribe agent. | None |
| `memory_store.py` | FAISS-backed in-memory vector store with SQLite persistence. | faiss, numpy |
| `ml/__init__.py` | No description | None |
| `ml/archetype_cluster.py` | No description | MUSIC_FOUNDATION, numpy, sklearn |
| `ml/data_pipeline.py` | No description | INANNA_AI |
| `ml/emotion_classifier.py` | No description | INANNA_AI, joblib, numpy, sklearn |
| `ml/evaluate_emotion_models.py` | No description | INANNA_AI |
| `modulation_arrangement.py` | Arrange and export audio stems produced by :mod:`vocal_isolation`. | audio |
| `monitoring/watchdog.py` | No description | os_guardian, prometheus_client, psutil |
| `music_generation.py` | Generate music from a text prompt using various models. | src, transformers |
| `music_llm_interface.py` | No description | INANNA_AI, numpy, rag, src |
| `nlq_api.py` | No description | agents, core, fastapi |
| `operator_api.py` | Operator command API exposing the :class:`OperatorDispatcher`. | agents, fastapi |
| `orchestration_master.py` | High-level orchestrator selecting agents and wiring memory stores. | memory, tools, yaml |
| `os_guardian/__init__.py` | Utilities for operating system automation. | None |
| `os_guardian/action_engine.py` | No description | pyautogui, selenium |
| `os_guardian/cli.py` | No description | None |
| `os_guardian/perception.py` | No description | cv2, numpy, pyautogui, pytesseract, ultralytics |
| `os_guardian/planning.py` | No description | langchain |
| `os_guardian/safety.py` | No description | None |
| `pipeline/__init__.py` | No description | None |
| `pipeline/music_analysis.py` | No description | INANNA_AI, audio, numpy |
| `prompt_engineering.py` | Prompt transformations based on style presets. | style_engine |
| `rag/__init__.py` | Retrieval-augmented generation helpers. | None |
| `rag/embedder.py` | No description | INANNA_AI, crown_config, numpy, sentence_transformers |
| `rag/engine.py` | No description | haystack, llama_index |
| `rag/music_oracle.py` | No description | INANNA_AI, audio |
| `rag/orchestrator.py` | Multimodal Generative Expression orchestrator. | INANNA_AI, SPIRAL_OS, audio, core, crown_config, numpy, sentence_transformers, soundfile, tools |
| `rag/parser.py` | No description | None |
| `rag/retriever.py` | No description | INANNA_AI, chromadb, memory, numpy |
| `razar/__init__.py` | Razar package hosting boot orchestration utilities. | None |
| `razar/__main__.py` | No description | agents |
| `razar/adaptive_orchestrator.py` | No description | yaml |
| `razar/boot_orchestrator.py` | Simple boot orchestrator reading a JSON component configuration. | None |
| `razar/checkpoint_manager.py` | Checkpoint utilities for the adaptive orchestrator. | None |
| `razar/cocreation_planner.py` | No description | yaml |
| `razar/crown_handshake.py` | No description | websockets |
| `razar/crown_link.py` | No description | websockets |
| `razar/doc_sync.py` | Synchronize Ignition, blueprint and component docs. | agents, yaml |
| `razar/environment_builder.py` | No description | yaml |
| `razar/health_checks.py` | Health check routines for Razar boot components. | None |
| `razar/issue_analyzer.py` | No description | None |
| `razar/mission_logger.py` | Lightweight proxy to :mod:`agents.razar.mission_logger`. | None |
| `razar/module_sandbox.py` | No description | None |
| `razar/quarantine_manager.py` | No description | None |
| `razar/recovery_manager.py` | No description | None |
| `razar/status_dashboard.py` | No description | razar, yaml |
| `recursive_emotion_router.py` | No description | labs, memory |
| `release.py` | Release utilities for the project. | None |
| `ritual_trainer.py` | No description | core, memory |
| `run_song_demo.py` | Demo runner for INANNA Music Composer AI. | MUSIC_FOUNDATION, yaml |
| `scripts/albedo_demo.py` | Command line demo for Albedo persona interactions. | agents |
| `scripts/bootstrap.py` | Bootstrap the development environment. | torch |
| `scripts/check_connector_index.py` | Ensure touched connectors have registry entries. | None |
| `scripts/check_key_documents.py` | Verify that key documents exist. | yaml |
| `scripts/check_no_binaries.py` | Fail if any staged files are detected as binary. | None |
| `scripts/check_no_placeholders.py` | Fail if files contain TODO or FIXME placeholders. | None |
| `scripts/component_inventory.py` | No description | None |
| `scripts/confirm_reading.py` | Ensure required onboarding documents have been read. | yaml |
| `scripts/data_validate.py` | Validate training data schema using TensorFlow Data Validation. | tensorflow_data_validation |
| `scripts/dependency_check.py` | Verify package imports and optional dependencies. | None |
| `scripts/ensure_blueprint_sync.py` | Verify blueprint doc updates accompany core code changes. | None |
| `scripts/export_coverage.py` | Export coverage metrics to component_index.json and enforce thresholds. | None |
| `scripts/generate_sbom.py` | Generate a CycloneDX software bill of materials. | None |
| `scripts/ingest_biosignals.py` | Ingest biosignal CSV files into the narrative engine. | memory |
| `scripts/ingest_music_books.py` | No description | pdfplumber, unstructured |
| `scripts/list_layers.py` | Print configured personality layers and whether they are enabled. | yaml |
| `scripts/offsite_backup.py` | Manage snapshot and restoration of off-site memory backups. | None |
| `scripts/quality_score.py` | Compute quality scores for repository components. | None |
| `scripts/record_feedback.py` | Log user feedback to the local database. | INANNA_AI |
| `scripts/replay_state.py` | Restore backups and rebuild vector memory from log files. | None |
| `scripts/show_emotion_glyph.py` | Display the last recorded emotion with its spiral glyph. | None |
| `scripts/train_distributed.py` | Distributed training example using PyTorch FSDP. | mlflow, omegaconf, optuna, torch |
| `scripts/validate_configs.py` | Validate YAML templates and JSON schema files. | jsonschema, yaml |
| `scripts/validate_schemas.py` | Validate JSON files against their JSON Schemas. | jsonschema |
| `scripts/vast_check.py` | No description | aiortc, httpx |
| `scripts/verify_doc_summaries.py` | Check onboarding doc summaries stay in sync with file hashes. | yaml |
| `servant_model_manager.py` | Registry and launcher for auxiliary language models. | tools |
| `server.py` | Minimal FastAPI server exposing health and utility endpoints. | INANNA_AI, PIL, agents, communication, connectors, core, crown_config, fastapi, memory, numpy, prometheus_client, prometheus_fastapi_instrumentator, pydantic, yaml |
| `seven_dimensional_music.py` | Utility for simple seven-dimensional music features. | MUSIC_FOUNDATION, numpy, src |
| `soul_state_manager.py` | Track the active archetype and soul state transitions. | None |
| `spiral_embedder.py` | No description | spiral_vector_db |
| `spiral_memory.py` | Cross-layer spiral memory with recursive recall and event registry. | memory, torch |
| `spiral_vector_db/__init__.py` | Simple wrapper around ChromaDB for storing text embeddings. | MUSIC_FOUNDATION, chromadb, numpy |
| `src/__init__.py` | Top-level package exposing core submodules. | None |
| `src/api/__init__.py` | Package initialization. | None |
| `src/api/server.py` | FastAPI server providing video generation and avatar streaming APIs. | audio, fastapi, prometheus_fastapi_instrumentator, style_engine |
| `src/audio/__init__.py` | No description | None |
| `src/audio/audio_ingestion.py` | No description | demucs, essentia, librosa, numpy, spleeter, torch, transformers |
| `src/audio/backends.py` | No description | core, numpy, simpleaudio, soundfile |
| `src/audio/check_env.py` | No description | None |
| `src/audio/dsp_engine.py` | No description | magenta, numpy, rave, soundfile, torch |
| `src/audio/emotion_params.py` | No description | INANNA_AI, MUSIC_FOUNDATION |
| `src/audio/engine.py` | Simple playback engine for ritual loops and voice audio. | MUSIC_FOUNDATION, audio, numpy, pydub, simpleaudio, soundfile |
| `src/audio/mix_tracks.py` | No description | MUSIC_FOUNDATION, numpy, soundfile, yaml |
| `src/audio/play_ritual_music.py` | Compose short ritual music based on emotion and play it. | numpy, yaml |
| `src/audio/segment.py` | No description | core, numpy |
| `src/audio/stego.py` | No description | MUSIC_FOUNDATION, numpy |
| `src/audio/voice_aura.py` | No description | audio, soundfile |
| `src/audio/voice_cloner.py` | No description | INANNA_AI, core, numpy |
| `src/audio/waveform.py` | No description | MUSIC_FOUNDATION, numpy, soundfile |
| `src/cli.py` | Unified command line interface for Spiral OS tools. | pytest |
| `src/cli/__init__.py` | Command-line interface utilities. | None |
| `src/cli/console_interface.py` | Interactive REPL for the Crown agent. | INANNA_AI, audio, core, memory, prompt_toolkit, rag, requests, tools |
| `src/cli/music_helper.py` | No description | INANNA_AI, tools |
| `src/cli/sandbox_helper.py` | No description | tools |
| `src/cli/spiral_cortex_terminal.py` | No description | memory |
| `src/cli/voice.py` | No description | INANNA_AI, connectors, core, cv2, httpx, numpy |
| `src/cli/voice_clone.py` | No description | audio |
| `src/cli/voice_clone_helper.py` | No description | INANNA_AI, audio |
| `src/core/__init__.py` | Core package exposing primary services. | None |
| `src/core/avatar_expression_engine.py` | Synchronise avatar expressions with audio playback. | audio, core, numpy |
| `src/core/code_introspector.py` | No description | None |
| `src/core/config.py` | Validated configuration loading using Pydantic. | pydantic, yaml |
| `src/core/context_tracker.py` | No description | None |
| `src/core/contracts.py` | No description | None |
| `src/core/emotion_analyzer.py` | No description | INANNA_AI |
| `src/core/expressive_output.py` | No description | audio, imageio, numpy |
| `src/core/facial_expression_controller.py` | No description | numpy |
| `src/core/feedback_logging.py` | Manage feedback logs and thresholds with on-disk persistence. | crown_config |
| `src/core/language_engine.py` | No description | INANNA_AI |
| `src/core/memory_logger.py` | No description | None |
| `src/core/memory_physical.py` | No description | core, soundfile |
| `src/core/model_selector.py` | No description | INANNA_AI |
| `src/core/self_correction_engine.py` | No description | INANNA_AI, numpy |
| `src/core/task_parser.py` | No description | None |
| `src/core/task_profiler.py` | No description | None |
| `src/core/utils/optional_deps.py` | Helpers for optional dependencies with lightweight stubs. | None |
| `src/core/utils/seed.py` | Utilities for deterministic behaviour. | numpy, torch |
| `src/core/video_engine.py` | No description | core, numpy |
| `src/dashboard/__init__.py` | Dashboard components for monitoring and mixing. | None |
| `src/dashboard/app.py` | Streamlit dashboard for visualising LLM performance. | pandas, streamlit |
| `src/dashboard/qnl_mixer.py` | Tools for mixing QNL audio inside Streamlit. | MUSIC_FOUNDATION, audio, librosa, matplotlib, numpy, soundfile, streamlit |
| `src/dashboard/rl_metrics.py` | Streamlit dashboard for reinforcement learning metrics. | INANNA_AI, pandas, streamlit |
| `src/dashboard/system_monitor.py` | System resource monitoring utilities. | psutil |
| `src/dashboard/usage.py` | Streamlit dashboard for usage metrics. | core, pandas, streamlit |
| `src/health/__init__.py` | Health check utilities for Spiral OS. | None |
| `src/health/boot_diagnostics.py` | Boot diagnostics for verifying essential services. | None |
| `src/health/essential_services.py` | List of core modules required for Spiral OS boot diagnostics. | None |
| `src/init_crown_agent.py` | Load Crown agent configuration and expose model endpoints. | yaml |
| `src/lwm/__init__.py` | No description | None |
| `src/lwm/config_model.py` | Configuration model for the Large World Model. | omegaconf |
| `src/lwm/large_world_model.py` | Minimal Large World Model converting 2D frames into a 3D scene. | None |
| `src/media/__init__.py` | Unified media interfaces for audio, video, and avatar. | None |
| `src/media/audio/__init__.py` | Audio generation and playback interface. | None |
| `src/media/audio/backends.py` | Utilities for loading optional audio backends. | None |
| `src/media/audio/base.py` | Audio-specific media processing interfaces. | None |
| `src/media/audio/generation.py` | Audio generation utilities with optional dependencies. | pydub |
| `src/media/audio/playback.py` | Audio playback utilities with optional dependencies. | ffmpeg |
| `src/media/avatar/__init__.py` | Avatar generation and playback interface. | None |
| `src/media/avatar/base.py` | Avatar-specific media processing interfaces. | None |
| `src/media/avatar/generation.py` | Avatar generation utilities composed from audio and video. | audio, lwm, video |
| `src/media/avatar/playback.py` | Avatar playback utilities. | audio, video |
| `src/media/base.py` | Common media processing interfaces. | None |
| `src/media/video/__init__.py` | Video generation and playback interface. | None |
| `src/media/video/base.py` | Video-specific media processing interfaces. | None |
| `src/media/video/generation.py` | Video generation utilities with optional dependencies. | ffmpeg, lwm |
| `src/media/video/playback.py` | Video playback utilities with optional dependencies. | ffmpeg |
| `src/spiral_os/__init__.py` | No description | None |
| `src/spiral_os/__main__.py` | Command-line interface for Spiral OS utilities. | yaml |
| `src/spiral_os/_hf_stub.py` | Minimal stub of the `huggingface_hub` package used in tests. | None |
| `src/spiral_os/start_spiral_os.py` | Launch the Spiral OS initialization sequence. | INANNA_AI, INANNA_AI_AGENT, connectors, core, dashboard, rag, tools, uvicorn, yaml |
| `start_crown_console.py` | Run Crown services and video stream with graceful shutdown. | dotenv |
| `start_dev_agents.py` | Command line launcher for the development agent cycle. | agents, memory, tools |
| `start_spiral_os.py` | Launch the Spiral OS initialization sequence. | INANNA_AI, INANNA_AI_AGENT, connectors, core, dashboard, health, rag, tools, uvicorn, yaml |
| `state_transition_engine.py` | Simple finite state engine based on emotional cues. | INANNA_AI |
| `style_engine/__init__.py` | Package initialization. | None |
| `style_engine/neural_style_transfer.py` | No description | numpy |
| `style_engine/style_library.py` | Utilities for loading video style configurations. | yaml |
| `task_profiling.py` | Compatibility wrappers around :class:`core.task_profiler.TaskProfiler`. | core |
| `tests/agents/nazarick/test_ethics_manifesto.py` | No description | agents |
| `tests/agents/nazarick/test_trust_matrix.py` | No description | agents |
| `tests/agents/razar/conftest.py` | Fixtures for RAZAR runtime tests. | agents, pytest, yaml |
| `tests/agents/razar/test_ai_invoker.py` | No description | agents |
| `tests/agents/razar/test_boot_sequence.py` | No description | pytest, razar |
| `tests/agents/razar/test_checkpoint_manager.py` | No description | agents |
| `tests/agents/razar/test_crown_link.py` | No description | agents, websockets |
| `tests/agents/razar/test_ignition_builder.py` | No description | agents |
| `tests/agents/razar/test_module_builder.py` | No description | agents |
| `tests/agents/razar/test_planning_engine.py` | No description | agents, yaml |
| `tests/agents/razar/test_pytest_runner.py` | No description | agents, pytest |
| `tests/agents/razar/test_quarantine_manager.py` | No description | agents |
| `tests/agents/razar/test_runtime_manager.py` | No description | agents, yaml |
| `tests/agents/razar/test_vision_adapter.py` | No description | agents, numpy |
| `tests/agents/test_asian_gen.py` | No description | agents, pytest |
| `tests/agents/test_bana.py` | No description | agents, numpy, pytest |
| `tests/agents/test_bana_narrator.py` | No description | agents, numpy, pytest, tests |
| `tests/agents/test_event_bus.py` | No description | agents, citadel |
| `tests/agents/test_land_graph_geo_knowledge.py` | No description | agents |
| `tests/agents/test_narrative_scribe.py` | No description | agents, citadel, memory |
| `tests/agents/test_razar_blueprint_synthesizer.py` | No description | None |
| `tests/agents/test_razar_cli.py` | No description | agents, pytest |
| `tests/conftest.py` | Pytest configuration and shared fixtures. | pytest, scipy, spiral_os |
| `tests/data/short_wav_base64.py` | No description | None |
| `tests/data/test1_wav_base64.py` | Tests for test1 wav base64. | None |
| `tests/helpers/config_stub.py` | Provide a minimal configuration object for tests. | None |
| `tests/helpers/emotion_stub.py` | Minimal stub for :mod:`INANNA_AI.emotion_analysis` used in tests. | None |
| `tests/helpers/mock_training_data.py` | No description | None |
| `tests/memory/test_cortex_concurrency.py` | Concurrency checks for cortex memory operations. | memory |
| `tests/memory/test_memory_store_fallback.py` | No description | None |
| `tests/memory/test_sharded_memory_store.py` | No description | numpy |
| `tests/memory/test_vector_memory.py` | Verify snapshot persistence and clustering for vector memory. | numpy, pytest |
| `tests/memory/test_vector_persistence.py` | Exercise FAISS/SQLite backed vector persistence. | numpy, pytest |
| `tests/narrative_engine/test_biosignal_pipeline.py` | Tests for biosignal ingestion and transformation. | memory, pytest, src |
| `tests/performance/test_task_parser_performance.py` | Tests for task parser performance. | None |
| `tests/performance/test_vector_memory_performance.py` | Tests for vector memory performance. | None |
| `tests/test_adaptive_learning.py` | Tests for adaptive learning. | INANNA_AI, pytest |
| `tests/test_adaptive_learning_stub.py` | Tests for adaptive learning stub. | None |
| `tests/test_albedo_layer.py` | Tests for albedo layer. | INANNA_AI |
| `tests/test_albedo_personality.py` | Tests for albedo personality. | INANNA_AI |
| `tests/test_albedo_state_machine.py` | No description | albedo |
| `tests/test_albedo_trust.py` | No description | agents, albedo, src |
| `tests/test_alchemical_persona.py` | Tests for alchemical persona. | INANNA_AI, numpy |
| `tests/test_api_endpoints.py` | Tests for api endpoints. | api, fastapi |
| `tests/test_archetype_feedback_loop.py` | Tests for archetype feedback loop. | memory |
| `tests/test_archetype_shift.py` | Tests for archetype shift. | None |
| `tests/test_audio_backends.py` | Tests for audio backends when soundfile is absent. | audio, numpy, pytest |
| `tests/test_audio_emotion_listener.py` | Tests for audio emotion listener. | INANNA_AI, numpy |
| `tests/test_audio_engine.py` | Tests for audio engine. | audio, pytest |
| `tests/test_audio_ingestion.py` | Tests for audio ingestion. | audio, numpy, pytest |
| `tests/test_audio_segment.py` | Tests for AudioSegment fallback to NpAudioSegment when soundfile is absent. | numpy |
| `tests/test_audio_tools.py` | Tests for audio tools. | INANNA_AI, librosa, numpy, pytest, tests |
| `tests/test_audio_video_sync_profile.py` | Tests for audio video sync profile. | numpy, pytest, src |
| `tests/test_auto_retrain.py` | Tests for auto retrain. | pytest, tests |
| `tests/test_autoretrain_full.py` | Tests for autoretrain full. | tests |
| `tests/test_avatar_console_startup.py` | Tests for avatar console startup. | pytest |
| `tests/test_avatar_expression_engine.py` | Tests for avatar expression engine. | audio, core, numpy |
| `tests/test_avatar_lipsync.py` | Tests for avatar lipsync. | numpy, pytest |
| `tests/test_avatar_pipeline.py` | Tests for avatar pipeline. | core, numpy |
| `tests/test_avatar_state_logging.py` | Tests for avatar state logging. | pytest, rag |
| `tests/test_avatar_stream_pipeline.py` | Tests for avatar stream pipeline. | INANNA_AI, audio, core, crown_config, fastapi, numpy, pytest, rag |
| `tests/test_avatar_voice.py` | Tests for avatar voice. | audio, core, numpy |
| `tests/test_benchmark.py` | Tests for benchmark. | INANNA_AI_AGENT |
| `tests/test_bootstrap.py` | Tests for the bootstrap script. | pytest, scripts |
| `tests/test_bots.py` | Tests for bots. | pytest, tools |
| `tests/test_citadel_event_processor.py` | No description | citadel |
| `tests/test_citadel_event_producer.py` | No description | citadel |
| `tests/test_citrinitas_cycle.py` | Tests for citrinitas cycle. | None |
| `tests/test_citrinitas_layer.py` | Tests for citrinitas layer. | INANNA_AI |
| `tests/test_citrinitas_ritual.py` | Tests for citrinitas ritual. | core, pytest |
| `tests/test_config_model.py` | Tests for the configuration model. | core |
| `tests/test_console_reflection.py` | Tests for console reflection. | pytest |
| `tests/test_console_sandbox_command.py` | Tests for /sandbox command in console interface. | None |
| `tests/test_core_scipy_smoke.py` | Smoke test ensuring core package and SciPy are importable. | core, scipy |
| `tests/test_core_services.py` | Tests for core services. | core, tests |
| `tests/test_corpus_logging.py` | No description | None |
| `tests/test_corpus_memory.py` | Tests for corpus memory. | INANNA_AI, numpy, pytest |
| `tests/test_corpus_memory_extended.py` | Tests for corpus memory extended. | INANNA_AI |
| `tests/test_corpus_memory_logging.py` | No description | None |
| `tests/test_cortex_memory.py` | Tests for cortex memory. | memory |
| `tests/test_cortex_sigil_logic.py` | Tests for cortex sigil logic. | labs |
| `tests/test_crown_config.py` | Tests for crown config. | crown_config |
| `tests/test_crown_console_startup.py` | Tests for crown console startup. | pytest |
| `tests/test_crown_decider.py` | Tests for crown decider. | None |
| `tests/test_crown_decider_history.py` | Tests for crown decider history. | None |
| `tests/test_crown_decider_rotation.py` | Tests for crown decider rotation. | None |
| `tests/test_crown_initialization.py` | Tests for crown initialization. | INANNA_AI, pytest |
| `tests/test_crown_prompt_orchestrator.py` | Tests for crown prompt orchestrator. | None |
| `tests/test_crown_query_router.py` | Tests for crown query router. | rag |
| `tests/test_crown_router_memory.py` | Tests for crown router memory. | pytest |
| `tests/test_crown_servant_registration.py` | Tests for crown servant registration. | INANNA_AI, pytest, yaml |
| `tests/test_dashboard_app.py` | Tests for dashboard app. | streamlit |
| `tests/test_dashboard_qnl_mixer.py` | Tests for dashboard qnl mixer. | numpy, streamlit |
| `tests/test_dashboard_usage.py` | Tests for dashboard usage. | None |
| `tests/test_data_pipeline.py` | Tests for data pipeline. | None |
| `tests/test_defensive_network_utils.py` | Tests for defensive network utils. | INANNA_AI, pytest |
| `tests/test_dependency_installer.py` | Tests for tools.dependency_installer via sandbox_session. | pytest, tools |
| `tests/test_deployment_configs.py` | No description | yaml |
| `tests/test_dev_orchestrator.py` | Tests for dev orchestrator. | pytest, tools |
| `tests/test_download_deepseek.py` | Tests for download deepseek. | pytest |
| `tests/test_download_model.py` | Tests for the DeepSeek model downloader. | pytest |
| `tests/test_download_models.py` | Tests for the model download utility. | pytest |
| `tests/test_dsp_engine.py` | Tests for dsp engine. | audio, numpy, pytest |
| `tests/test_emotion_classifier.py` | Tests for emotion classifier. | ml, numpy, pytest |
| `tests/test_emotion_loop.py` | Tests for emotion loop. | core, pytest |
| `tests/test_emotion_music_map.py` | Tests for emotion music map. | MUSIC_FOUNDATION |
| `tests/test_emotion_registry.py` | Tests for emotion registry. | pytest, yaml |
| `tests/test_emotion_state.py` | Concurrency and persistence tests for emotional_state. | pytest |
| `tests/test_emotional_memory.py` | Tests for emotional memory. | INANNA_AI |
| `tests/test_emotional_state.py` | Tests for emotional state. | pytest |
| `tests/test_emotional_state_logging.py` | Smoke test for emotion event logging. | pytest |
| `tests/test_emotional_synaptic_engine.py` | Tests for emotional synaptic engine. | INANNA_AI |
| `tests/test_emotional_voice.py` | Tests for emotional voice. | INANNA_AI |
| `tests/test_enlightened_prompt.py` | Tests for enlightened prompt builder. | INANNA_AI, numpy |
| `tests/test_env_validation.py` | Tests for env validation. | pytest |
| `tests/test_ethical_validator.py` | Tests for ethical validator. | INANNA_AI, pytest |
| `tests/test_existential_reflector.py` | Tests for existential reflector. | INANNA_AI, INANNA_AI_AGENT |
| `tests/test_expressive_output.py` | Tests for expressive output. | core, numpy |
| `tests/test_feedback_logging.py` | Tests for feedback logging. | INANNA_AI |
| `tests/test_full_audio_pipeline.py` | Tests for full audio pipeline. | SPIRAL_OS, audio, numpy, pytest |
| `tests/test_gateway.py` | Tests for gateway. | communication |
| `tests/test_github_metadata.py` | Tests for github metadata. | INANNA_AI |
| `tests/test_github_scraper.py` | Tests for github scraper. | INANNA_AI |
| `tests/test_github_scraper_enhanced.py` | Tests for github scraper enhanced. | INANNA_AI |
| `tests/test_glm_command.py` | Test the GLM command endpoint authorization and command filtering. | crown_config, httpx, pytest |
| `tests/test_glm_modules.py` | Tests for glm modules. | INANNA_AI, pytest |
| `tests/test_glm_shell.py` | Tests for glm shell. | INANNA_AI, pytest |
| `tests/test_hex_to_glyphs_smoke.py` | No description | SPIRAL_OS, numpy |
| `tests/test_inanna_ai.py` | Tests for inanna ai. | INANNA_AI, INANNA_AI_AGENT, pytest |
| `tests/test_inanna_music_cli.py` | Tests for inanna music cli. | tests |
| `tests/test_inanna_voice.py` | Tests for inanna voice. | pytest |
| `tests/test_initial_listen.py` | Tests for initial listen. | pytest |
| `tests/test_insight_compiler.py` | Tests for insight compiler. | jsonschema |
| `tests/test_integrity.py` | Tests for integrity. | INANNA_AI, OpenSSL, numpy, pytest |
| `tests/test_interactions_jsonl.py` | Tests for logging sample interactions to JSONL. | None |
| `tests/test_interactions_jsonl_integrity.py` | Additional JSONL integrity tests for interaction logging. | None |
| `tests/test_interconnectivity.py` | Tests for interconnectivity. | core, rag |
| `tests/test_introspection_api.py` | Tests for introspection api. | fastapi, pytest |
| `tests/test_invocation_engine.py` | Tests for invocation engine. | None |
| `tests/test_kimi_k2_servant.py` | Tests for kimi k2 servant. | INANNA_AI, yaml |
| `tests/test_kimi_servant.py` | Tests for kimi servant. | tools |
| `tests/test_language_model_layer.py` | Tests for language model layer. | None |
| `tests/test_launch_servants_script.py` | Tests for launch servants script. | pytest |
| `tests/test_learning.py` | Tests for learning. | INANNA_AI |
| `tests/test_learning_mutator.py` | Tests for learning mutator. | pytest, tests |
| `tests/test_learning_mutator_personality.py` | Tests for learning mutator personality. | None |
| `tests/test_lip_sync.py` | Tests for lip sync. | ai_core |
| `tests/test_listening_engine.py` | Tests for listening engine. | INANNA_AI, numpy |
| `tests/test_logging_config_rotation.py` | No description | yaml |
| `tests/test_logging_filters.py` | Tests for logging filters. | None |
| `tests/test_lwm.py` | Tests for LWM integration and inspection routes. | fastapi, pytest, src |
| `tests/test_lwm_config.py` | Tests for the LWM configuration model. | lwm, pytest |
| `tests/test_media_audio.py` | Regression tests for media.audio package. | pytest, src |
| `tests/test_media_avatar.py` | Regression tests for media.avatar package. | pytest, src |
| `tests/test_media_video.py` | Regression tests for media.video module. | pytest, src |
| `tests/test_memory_emotional.py` | Tests for memory emotional. | memory, pytest |
| `tests/test_memory_persistence.py` | Test concurrent vector memory persistence and recovery. | fakeredis, pytest |
| `tests/test_memory_search.py` | Tests for memory search. | memory |
| `tests/test_memory_snapshot.py` | Tests for memory snapshot. | None |
| `tests/test_memory_spiritual.py` | Tests for the spiritual memory ontology database. | memory |
| `tests/test_memory_store.py` | Tests for memory store. | numpy |
| `tests/test_mission_logger.py` | No description | razar |
| `tests/test_mix_tracks.py` | Tests for mix tracks. | audio, numpy, soundfile |
| `tests/test_mix_tracks_emotion.py` | Tests for mix tracks emotion. | audio, numpy |
| `tests/test_mix_tracks_instructions.py` | Tests for mix tracks instructions. | audio, numpy, soundfile |
| `tests/test_model.py` | Tests for model. | pytest, tokenizers, transformers |
| `tests/test_model_benchmarking.py` | Tests for model benchmarking. | INANNA_AI, core, rag, tests |
| `tests/test_modulation_arrangement.py` | Tests for modulation arrangement. | pytest |
| `tests/test_music_analysis_pipeline.py` | Tests for music analysis pipeline. | numpy |
| `tests/test_music_backends_missing.py` | Tests for graceful backend fallbacks. | numpy, pytest |
| `tests/test_music_generation.py` | Tests for music generation. | pytest |
| `tests/test_music_generation_emotion.py` | Tests for music generation emotion. | pytest |
| `tests/test_music_generation_missing_pipeline.py` | Tests for missing transformers pipeline. | pytest |
| `tests/test_music_generation_streaming.py` | Additional tests for music generation streaming and parameters. | pytest, src |
| `tests/test_music_memory.py` | Tests for music memory. | memory, numpy |
| `tests/test_nazarick_messaging.py` | No description | agents, albedo |
| `tests/test_network_schedule.py` | Tests for network schedule. | INANNA_AI |
| `tests/test_network_utils.py` | Tests for network utils. | INANNA_AI |
| `tests/test_nigredo_layer.py` | Tests for nigredo layer. | INANNA_AI |
| `tests/test_openwebui_state_updates.py` | No description | httpx, tests |
| `tests/test_optional_imports.py` | Tests for optional imports. | None |
| `tests/test_orchestration_master.py` | Tests for orchestration master optional agents. | src |
| `tests/test_orchestrator.py` | Tests for orchestrator. | core, rag, tests |
| `tests/test_orchestrator_crown_music.py` | Tests for orchestrator crown music. | numpy, rag |
| `tests/test_orchestrator_handle.py` | Tests for orchestrator handle. | pytest, rag |
| `tests/test_orchestrator_integration.py` | Tests for orchestrator integration. | core, rag, tests |
| `tests/test_orchestrator_memory.py` | Tests for orchestrator memory. | rag |
| `tests/test_orchestrator_routing.py` | Tests for orchestrator routing. | crown_config, numpy, rag |
| `tests/test_orchestrator_suggestions_logging.py` | Tests for orchestrator suggestions logging. | rag |
| `tests/test_os_guardian.py` | Tests for os guardian. | None |
| `tests/test_os_guardian_action_engine.py` | Tests for os guardian action engine. | None |
| `tests/test_os_guardian_perception.py` | Tests for os guardian perception. | None |
| `tests/test_os_guardian_planning.py` | Tests for os guardian planning. | None |
| `tests/test_personality_layers.py` | Tests for personality layers. | INANNA_AI, pytest |
| `tests/test_phoneme_blendshape_alignment.py` | Integration tests for phoneme extraction and blendshape mapping. | ai_core |
| `tests/test_pipeline_cli.py` | Tests for pipeline cli. | None |
| `tests/test_play_ritual_music.py` | Tests for play ritual music. | audio, numpy |
| `tests/test_play_ritual_music_smoke.py` | Smoke test for ritual music playback. | audio, numpy, pytest |
| `tests/test_predictive_gate.py` | Tests for predictive gate. | INANNA_AI |
| `tests/test_preprocess.py` | Tests for preprocess. | INANNA_AI_AGENT, numpy |
| `tests/test_project_audit.py` | Tests for project audit. | tools |
| `tests/test_project_gutenberg.py` | Tests for project gutenberg. | INANNA_AI |
| `tests/test_prompt_engineering.py` | Tests for prompt engineering. | None |
| `tests/test_qnl_audio_pipeline.py` | Tests for qnl audio pipeline. | INANNA_AI_AGENT, audio, numpy, pytest |
| `tests/test_qnl_engine.py` | Tests for qnl engine. | SPIRAL_OS, numpy |
| `tests/test_qnl_parser.py` | Tests for qnl parser. | SPIRAL_OS |
| `tests/test_qnl_utils.py` | Tests for qnl utils. | MUSIC_FOUNDATION, numpy |
| `tests/test_quarantine_manager.py` | No description | pytest, razar |
| `tests/test_rag_embedder.py` | Tests for rag embedder. | rag |
| `tests/test_rag_engine.py` | Tests for rag engine. | pytest |
| `tests/test_rag_music_integration.py` | Tests for rag music integration. | SPIRAL_OS, rag |
| `tests/test_rag_music_oracle.py` | Tests for rag music oracle. | rag, tests |
| `tests/test_rag_parser.py` | Tests for rag parser. | rag |
| `tests/test_rag_retriever.py` | Tests for rag retriever. | numpy, rag |
| `tests/test_razar_health_checks.py` | No description | razar |
| `tests/test_recursive_emotion_router.py` | Tests for recursive emotion router. | None |
| `tests/test_reflection_integration.py` | Tests for reflection integration. | rag |
| `tests/test_reflection_thresholds_env.py` | Tests for reflection thresholds env. | tools |
| `tests/test_remote_loader.py` | No description | None |
| `tests/test_response_manager.py` | Tests for response manager. | INANNA_AI |
| `tests/test_retrain_and_deploy.py` | Tests for retrain and deploy. | INANNA_AI |
| `tests/test_retrain_model.py` | Tests for retrain model. | None |
| `tests/test_ritual_cli.py` | Tests for ritual cli. | None |
| `tests/test_rival_messaging.py` | No description | agents, albedo, src |
| `tests/test_rl_metrics.py` | Tests for rl metrics. | INANNA_AI |
| `tests/test_root_chakra_integration.py` | Tests for root chakra integration. | INANNA_AI, INANNA_AI_AGENT, dashboard |
| `tests/test_root_metrics_logging.py` | Tests for root metrics logging. | None |
| `tests/test_rubedo_layer.py` | Tests for rubedo layer. | INANNA_AI |
| `tests/test_run_inanna_sh.py` | Tests for run inanna sh. | pytest |
| `tests/test_run_song_demo.py` | Tests for run song demo. | tests |
| `tests/test_sandbox_session.py` | Tests for tools.sandbox_session. | tools |
| `tests/test_schema_validation.py` | No description | jsonschema |
| `tests/test_security_canary.py` | No description | agents |
| `tests/test_self_correction_engine.py` | Tests for self correction engine. | core |
| `tests/test_servant_model_manager.py` | Tests for servant model manager. | None |
| `tests/test_server.py` | Tests for server. | crown_config, fastapi, httpx, numpy |
| `tests/test_server_endpoints.py` | Exercise lightweight server endpoints. | crown_config, fastapi, pytest |
| `tests/test_session_logger.py` | Tests for session logger. | tools |
| `tests/test_seven_dimensional_music.py` | Tests for seven dimensional music. | MUSIC_FOUNDATION, SPIRAL_OS, numpy, soundfile |
| `tests/test_seven_plane_analyzer.py` | Tests for seven plane analyzer. | MUSIC_FOUNDATION, numpy, soundfile |
| `tests/test_silence_reflection.py` | Tests for silence reflection. | INANNA_AI, numpy |
| `tests/test_silence_ritual.py` | Tests for silence ritual. | rag |
| `tests/test_smoke_imports.py` | No description | agents, src |
| `tests/test_sonic_emotion_mapper.py` | Tests for sonic emotion mapper. | INANNA_AI |
| `tests/test_soul_ritual.py` | Tests for soul ritual. | INANNA_AI, pytest, tests |
| `tests/test_soul_state_manager.py` | Tests for soul state manager. | None |
| `tests/test_source_loader.py` | Tests for source loader. | INANNA_AI_AGENT |
| `tests/test_speaking_behavior.py` | Tests for speaking behavior. | INANNA_AI |
| `tests/test_speaking_engine.py` | Tests for speaking engine. | INANNA_AI, numpy |
| `tests/test_speaking_engine_streaming.py` | Tests for speaking engine streaming. | INANNA_AI, numpy |
| `tests/test_speech_loopback_reflector.py` | Tests for speech loopback reflector. | INANNA_AI |
| `tests/test_spiral_cortex_integration.py` | Tests for spiral cortex integration. | memory |
| `tests/test_spiral_cortex_memory.py` | Tests for spiral cortex memory. | memory, rag, tests |
| `tests/test_spiral_memory.py` | Tests for spiral memory. | None |
| `tests/test_spiral_os.py` | Tests for the spiral_os CLI pipeline utility. | pytest, yaml |
| `tests/test_spiral_rag.py` | Tests for spiral rag. | rag |
| `tests/test_spiral_vector_db.py` | Tests for spiral vector db. | numpy |
| `tests/test_start_avatar_console.py` | Tests for start avatar console. | pytest |
| `tests/test_start_crown_console_py.py` | Tests for start crown console py. | None |
| `tests/test_start_crown_console_trap.py` | Tests for start crown console trap. | pytest |
| `tests/test_start_dev_agents_triage.py` | Tests for start dev agents triage. | None |
| `tests/test_start_spiral_os.py` | Tests for start spiral os. | pytest, tests |
| `tests/test_state_transition_engine.py` | Tests for state transition engine. | None |
| `tests/test_style_selection.py` | Tests for style selection. | ai_core, style_engine |
| `tests/test_suggest_enhancement.py` | Tests for suggest enhancement. | INANNA_AI_AGENT |
| `tests/test_symbolic_parser.py` | Tests for symbolic parser. | SPIRAL_OS |
| `tests/test_synthetic_stego.py` | Tests for synthetic stego. | MUSIC_FOUNDATION, numpy, soundfile |
| `tests/test_synthetic_stego_engine.py` | Tests for synthetic stego engine. | MUSIC_FOUNDATION, numpy |
| `tests/test_system_monitor.py` | Tests for system monitor. | dashboard |
| `tests/test_task_parser.py` | Tests for task parser. | None |
| `tests/test_task_profiling.py` | Tests for task profiling. | core |
| `tests/test_task_profiling_wrappers.py` | No description | core |
| `tests/test_tools_smoke.py` | No description | numpy, tools |
| `tests/test_training_feedback.py` | Tests for training feedback. | tests |
| `tests/test_training_guide.py` | Tests for training guide. | INANNA_AI |
| `tests/test_training_guide_logger.py` | Tests for training guide logger. | tests |
| `tests/test_training_guide_parser.py` | Tests for training guide parser. | INANNA_AI |
| `tests/test_training_guide_trigger.py` | Tests for training guide trigger. | tests |
| `tests/test_transformation_smoke.py` | Smoke tests for transformation engines. | None |
| `tests/test_trust_registry.py` | No description | memory |
| `tests/test_tts_backends.py` | Tests for tts backends. | INANNA_AI, crown_config |
| `tests/test_utils_verify_insight_matrix.py` | Tests for utils verify insight matrix. | INANNA_AI, pytest |
| `tests/test_vast_check.py` | Tests for vast check. | aiortc, fastapi, httpx |
| `tests/test_vast_pipeline.py` | Tests for vast pipeline. | SPIRAL_OS, aiortc, connectors, core, crown_config, fastapi, httpx, numpy, rag |
| `tests/test_vector_memory.py` | Tests for vector memory. | numpy, pytest |
| `tests/test_vector_memory_extensions.py` | Integration tests for extended vector memory features. | numpy, pytest, src |
| `tests/test_vector_memory_persistence.py` | No description | None |
| `tests/test_video.py` | Tests for video. | core, numpy, pytest |
| `tests/test_video_stream.py` | Tests for the WebRTC video and audio streaming endpoints. | aiortc, crown_config, fastapi, httpx, numpy, pytest |
| `tests/test_video_stream_audio.py` | Tests for video stream audio. | aiortc, crown_config, fastapi, httpx, numpy, pytest, soundfile |
| `tests/test_video_stream_helpers.py` | Tests for video stream helper utilities. | numpy |
| `tests/test_virtual_env_manager.py` | Tests for tools.virtual_env_manager. | tools |
| `tests/test_vocal_isolation.py` | Tests for vocal isolation. | None |
| `tests/test_voice_aura.py` | Tests for voice aura. | audio, numpy, pytest |
| `tests/test_voice_avatar_pipeline.py` | Tests for voice avatar pipeline. | INANNA_AI, INANNA_AI_AGENT, core, crown_config, numpy, tools |
| `tests/test_voice_cloner_cli.py` | Tests for voice cloning CLI and API using stubbed dependencies. | fastapi, numpy, src |
| `tests/test_voice_config.py` | Tests for voice config. | INANNA_AI |
| `tests/test_voice_conversion.py` | Tests for voice conversion. | INANNA_AI, crown_config, tools |
| `tests/test_voice_evolution.py` | Tests for voice evolution. | INANNA_AI, numpy |
| `tests/test_voice_evolution_memory.py` | Tests for voice evolution memory. | INANNA_AI |
| `tests/test_voice_layer_albedo.py` | Tests for voice layer albedo. | INANNA_AI |
| `tests/test_voice_profiles.py` | Tests for voice profiles. | INANNA_AI |
| `tests/test_webrtc_connector.py` | Tests for webrtc connector. | aiortc, connectors, crown_config, fastapi, httpx, tests |
| `tests/vision/test_yoloe_adapter.py` | No description | numpy, src |
| `tools/__init__.py` | Developer tooling utilities. | None |
| `tools/bot_discord.py` | No description | core, discord, requests |
| `tools/bot_telegram.py` | No description | core, requests |
| `tools/dependency_audit.py` | No description | tomli |
| `tools/dependency_installer.py` | No description | None |
| `tools/dev_orchestrator.py` | No description | INANNA_AI, autogen |
| `tools/doc_indexer.py` | Generate an index of Markdown documentation files. | None |
| `tools/kimi_k2_client.py` | No description | requests |
| `tools/preflight.py` | No description | None |
| `tools/project_audit.py` | No description | None |
| `tools/reflection_loop.py` | Mirror reflection loop utilities. | INANNA_AI, core, cv2, numpy |
| `tools/sandbox_session.py` | Helpers for working with sandboxed repository copies. | None |
| `tools/session_logger.py` | Utility functions to log session audio and video. | imageio, numpy |
| `tools/virtual_env_manager.py` | Utilities for working with Python virtual environments. | None |
| `tools/voice_conversion.py` | Command line wrappers for voice conversion tools. | None |
| `training_guide.py` | Log intent outcomes for reinforcement learning. | INANNA_AI, crown_config |
| `transformers/__init__.py` | Lightweight transformer stubs for testing. | None |
| `vector_memory.py` | FAISS/SQLite-backed text vector store with decay and operation logging. | MUSIC_FOUNDATION, crown_config, faiss, memory, numpy, sklearn |
| `video_stream.py` | Provide WebRTC streaming for avatar audio and video. | aiortc, core, fastapi, numpy, soundfile, src |
| `vision/__init__.py` | Vision utilities and adapters. | None |
| `vision/yoloe_adapter.py` | No description | numpy, ultralytics |
| `vocal_isolation.py` | Helpers for isolating vocals and other stems using external tools. | src |
