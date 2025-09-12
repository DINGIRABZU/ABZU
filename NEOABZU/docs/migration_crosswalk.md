# Migration Crosswalk

This guide maps legacy Python subsystems to their Rust implementations in NEOABZU.

| Python Subsystem | Rust Crate | Bridge |
| --- | --- | --- |
| `memory` layers (`memory/`, `vector_memory.py`) | `neoabzu-memory` | PyO3 module `neoabzu_memory` bundles cortex, vector, spiral, emotional, mental, spiritual, and narrative layers. |
| `crown_router.py` | `neoabzu-crown` | Exposes routing functions via `crown_router_rs.py` wrapper. |
| `rag/orchestrator.py` | `neoabzu-rag` | Provides retrieval utilities compatible with the RAG orchestrator. |

## PyO3 Integration Example

Legacy modules can import Rust crates compiled with PyO3 directly:

```python
from crown_router_rs import route_decision

result = route_decision("align chakras", {"emotion": "joy"})
print(result)
```

## HTTP API Example

When Rust crates run as standalone services, Python modules call them over HTTP:

```python
import requests

payload = {"question": "where are the logs?", "top_n": 3}
response = requests.post("http://localhost:8000/rag/retrieve_top", json=payload)
print(response.json())
```
