# Crown Servant Models

Guidance for deploying auxiliary servant models used by Crown.

## Overview
Servant models complement the primary GLM by handling specialized tasks. Each
servant runs as an independent process and exposes a `/health` endpoint so the
orchestrator can verify readiness.

## Configuration
Define servants in configuration files or environment variables. A minimal YAML
example:

```yaml
servants:
  kimi_k2:
    command: ["python", "kimi_k2_server.py"]
    health_url: "http://localhost:8000/health"
  opencode:
    command: ["python", "opencode_server.py"]
    health_url: "http://localhost:8001/health"
```

## Memory and Prompt Context
Servant models operate solely on the prompt text they receive. They do not
share Crown's vector or spiral memory layers. If additional context is needed,
call `query_memory` and prepend the returned data to the servant prompt before
dispatching the request.

```python
from memory.query_memory import query_memory

results = query_memory("latest project status")
prompt = f"{results['spiral']}\n\n{user_prompt}"
```

See [memory/query_memory.py](../memory/query_memory.py) for retrieval examples.

## Deployment Steps
1. **Download weights**
   ```bash
   python scripts/manage_servants.py download kimi_k2 https://example.com/kimi.bin models/kimi.bin
   ```
2. **Start the servant**
   ```bash
   python scripts/manage_servants.py start kimi_k2 -- python kimi_k2_server.py
   ```
3. **Health check**
   ```bash
   python scripts/manage_servants.py health kimi_k2 http://localhost:8000/health
   ```
4. **Stop the servant**
   ```bash
   python scripts/manage_servants.py stop kimi_k2
   ```

Health status is stored in `data/servant_state.json` and consulted by the crown
prompt orchestrator before routing requests.

## Version History
- **0.1.0** – Initial servant deployment guide.

## Patent Status

Covered in [PATENTS.md](../PATENTS.md) under "Crown Servant Orchestration." Draft filings, if any, reside in [patents/](../patents/). Substantive edits require maintainer approval.
