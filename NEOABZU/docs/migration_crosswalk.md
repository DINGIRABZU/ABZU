# Migration Crosswalk

This guide maps legacy Python subsystems to their Rust implementations in NEOABZU.

For narrative alignment and sacred terminology, consult [herojourney_engine.md](herojourney_engine.md) and [SUMERIAN_33WORDS.md](SUMERIAN_33WORDS.md).

| Python Subsystem | Rust Crate | Bridge |
| --- | --- | --- |
| `memory` layers (`memory/`, `vector_memory.py`) | `neoabzu-memory` | PyO3 module `neoabzu_memory` bundles cortex, vector, spiral, emotional, mental, spiritual, and narrative layers. |
| `crown_router.py` | `neoabzu-crown` | Exposes routing functions via `crown_router_rs.py` wrapper. |
| `rag/orchestrator.py` | `neoabzu-rag` | Provides retrieval utilities compatible with the RAG orchestrator. |
| `core` lambda engine (`core/`) | `neoabzu-core` | Accessible through `neoabzu_memory.eval_core` and `neoabzu_memory.reduce_inevitable_core` for Crown Router and RAZAR. |

## PyO3 Integration Example

Legacy modules can import Rust crates compiled with PyO3 directly:

```python
from crown_router_rs import route_decision

from neoabzu_memory import eval_core

result = route_decision("align chakras", {"emotion": "joy"})
print(result)

print(eval_core("(\\x.x)y"))
```

## HTTP API Example

When Rust crates run as standalone services, Python modules call them over HTTP:

```python
import requests

payload = {"question": "where are the logs?", "top_n": 3}
response = requests.post("http://localhost:8000/rag/retrieve_top", json=payload)
print(response.json())
```

## Cross-Stack Flow

Crown Router invokes `neoabzu_memory.eval_core` for lambda-calculus evaluation, while RAZAR calls `neoabzu_memory.reduce_inevitable_core` to gauge inevitability gradients during mission planning.
