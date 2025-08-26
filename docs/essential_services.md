# Essential Services

This guide highlights vital Spiral OS workflows, their fallback logic, and recovery steps.

## Health Monitoring
- **Workflow:** `scripts/vast_check.py` probes `/health`, `/ready`, and performs a dummy WebRTC offer.
- **Fallback:** If any probe fails, restart the server or verify network settings.
- **Recovery:** Inspect logs, ensure dependencies are installed, and relaunch `start_spiral_os.py`.

## Model Invocation
- **Workflow:** `crown_model_launcher.sh` and `init_crown_agent.py` load language and audio models.
- **Fallback:** When weights are missing, disable dependent features or switch to lightweight stubs.
- **Recovery:** Fetch weights with `download_models.py`, confirm GPU resources, and restart services.

## Memory Persistence
- **Workflow:** `vector_memory.py` and `memory_store.py` persist embeddings to the vector database.
- **Fallback:** If the database is unreachable, cache items locally and retry.
- **Recovery:** Restore the database, run integrity checks, and replay deferred writes.
