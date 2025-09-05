# Failure Inventory

Failures from `pytest` runs are appended via [`scripts/capture_failing_tests.py`](../../scripts/capture_failing_tests.py).

## Failures
- 2025-09-04: ERROR: usage: pytest [options] [file_or_dir] [file_or_dir] [...]
- 2025-09-04: No failures detected.

- 2025-09-04: ModuleNotFoundError: No module named "websockets" (tests/agents/razar/test_crown_link.py)

- 2025-09-04: ERROR    nlq_api:nlq_api.py:35 failed to train Vanna on schemas/channel_schema.sql
- 2025-09-04: ERROR    nlq_api:nlq_api.py:35 failed to train Vanna on schemas/timescaledb_agent_events.sql
- 2025-09-04: ERROR    nlq_api:nlq_api.py:35 failed to train Vanna on schemas/log_schema.sql
- 2025-09-04: ERROR    fastapi:utils.py:114 Form data requires "python-multipart" to be installed.
- 2025-09-04: ERROR    fastapi:utils.py:114 Form data requires "python-multipart" to be installed.
- 2025-09-04: ERROR    fastapi:utils.py:114 Form data requires "python-multipart" to be installed.
- 2025-09-04: ERROR tests/agents/razar/test_crown_link.py
- 2025-09-04: ERROR tests/crown/server/test_server.py - RuntimeError: Form data requires "python-multipart" to be installed.
- 2025-09-04: ERROR tests/crown/test_orchestrator_music.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-04: ERROR tests/integration/test_core_regressions.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-04: ERROR tests/narrative_engine/test_biosignal_transformation.py
- 2025-09-04: ERROR tests/narrative_engine/test_dataset_hashes.py
- 2025-09-04: ERROR tests/narrative_engine/test_event_storage.py
- 2025-09-04: ERROR tests/narrative_engine/test_ingest_persist_retrieve.py
- 2025-09-04: ERROR tests/narrative_engine/test_ingestion_to_mistral_output.py
- 2025-09-04: ERROR tests/narrative_engine/test_jsonl_ingest_persist_retrieve.py
- 2025-09-04: ERROR tests/razar/test_ai_invoker.py
- 2025-09-04: ERROR tests/root/test_metrics_logging.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-04: ERROR tests/test_auto_retrain.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-04: ERROR tests/test_autoretrain_full.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-04: ERROR tests/test_avatar_state_logging.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-04: ERROR tests/test_boot_sequence.py
- 2025-09-04: ERROR tests/test_dashboard_app.py - AttributeError: 'str' object has no attribute 'dtype'
- 2025-09-04: ERROR tests/test_dashboard_qnl_mixer.py - AttributeError: 'str' object has no attribute 'dtype'
- 2025-09-04: ERROR tests/test_emotion_classifier.py - AttributeError: 'types.SimpleNamespace' object has no attribute 'RandomState'
- 2025-09-04: ERROR tests/test_initial_listen.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-04: ERROR tests/test_interconnectivity.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-04: ERROR tests/test_mix_tracks.py
- 2025-09-04: ERROR tests/test_openwebui_state_updates.py
- 2025-09-04: ERROR tests/test_operator_api.py - RuntimeError: Form data requires "python-multipart" to be installed.
- 2025-09-04: ERROR tests/test_operator_command_route.py - RuntimeError: Form data requires "python-multipart" to be installed.
- 2025-09-04: ERROR tests/test_quarantine_manager.py
- 2025-09-04: ERROR tests/test_retrain_and_deploy.py
- 2025-09-04: ERROR tests/test_retrain_model.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-04: ERROR tests/test_spiral_cortex_memory.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-04: ERROR tests/test_transformers_generate.py - ValueError: cv2.__spec__ is None
- 2025-09-04: ERROR tests/test_vector_memory.py
- 2025-09-04: ERROR tests/test_voice_cloner_cli.py

- 2025-09-04: AttributeError: module "feedback_logging" has no attribute "NOVELTY_THRESHOLD" (tests/crown/test_orchestrator_music.py)

- 2025-09-05: ERROR: usage: pytest [options] [file_or_dir] [file_or_dir] [...]

- 2025-09-05: ERROR    nlq_api:nlq_api.py:35 failed to train Vanna on schemas/log_schema.sql
- 2025-09-05: ERROR    nlq_api:nlq_api.py:35 failed to train Vanna on schemas/channel_schema.sql
- 2025-09-05: ERROR    nlq_api:nlq_api.py:35 failed to train Vanna on schemas/timescaledb_agent_events.sql
- 2025-09-05: ERROR tests/crown/test_orchestrator_music.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-05: ERROR tests/integration/test_core_regressions.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-05: ERROR tests/narrative_engine/test_biosignal_transformation.py
- 2025-09-05: ERROR tests/narrative_engine/test_dataset_hashes.py
- 2025-09-05: ERROR tests/narrative_engine/test_event_storage.py
- 2025-09-05: ERROR tests/narrative_engine/test_ingest_persist_retrieve.py
- 2025-09-05: ERROR tests/narrative_engine/test_ingestion_to_mistral_output.py
- 2025-09-05: ERROR tests/narrative_engine/test_jsonl_ingest_persist_retrieve.py
- 2025-09-05: ERROR tests/razar/test_ai_invoker.py
- 2025-09-05: ERROR tests/root/test_metrics_logging.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-05: ERROR tests/test_auto_retrain.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-05: ERROR tests/test_autoretrain_full.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-05: ERROR tests/test_avatar_state_logging.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-05: ERROR tests/test_boot_sequence.py
- 2025-09-05: ERROR tests/test_dashboard_app.py - AttributeError: 'str' object has no attribute 'dtype'
- 2025-09-05: ERROR tests/test_dashboard_qnl_mixer.py - AttributeError: 'str' object has no attribute 'dtype'
- 2025-09-05: ERROR tests/test_emotion_classifier.py - AttributeError: 'types.SimpleNamespace' object has no attribute 'RandomState'
- 2025-09-05: ERROR tests/test_initial_listen.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-05: ERROR tests/test_interconnectivity.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-05: ERROR tests/test_mix_tracks.py
- 2025-09-05: ERROR tests/test_openwebui_state_updates.py
- 2025-09-05: ERROR tests/test_quarantine_manager.py
- 2025-09-05: ERROR tests/test_retrain_and_deploy.py
- 2025-09-05: ERROR tests/test_retrain_model.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-05: ERROR tests/test_spiral_cortex_memory.py - AttributeError: module 'feedback_logging' has no attribute 'NOVELTY_THRESHOLD'
- 2025-09-05: ERROR tests/test_transformers_generate.py - ValueError: cv2.__spec__ is None
- 2025-09-05: ERROR tests/test_vector_memory.py
- 2025-09-05: ERROR tests/test_voice_cloner_cli.py

- 2025-09-05: ERROR    __main__:app.py:30 Failed to fetch benchmarks: db down
- 2025-09-05: ERROR    __main__:app.py:49 Failed to predict best model: boom

- 2025-09-05: No failures detected.
