# Dependency Risks

This document outlines the impact of missing optional dependencies and ways to mitigate them.

## Optional Components

| Component | Dependency | Severity | Mitigation |
| --- | --- | --- | --- |
| vector_memory | faiss | high | Install `faiss-cpu` or `faiss-gpu` to enable efficient vector search. |
| rag | omegaconf | medium | `pip install omegaconf` to restore configuration support. |

Missing dependencies reduce component scores in `scripts/dependency_check.py` and may degrade functionality. Ensure optional packages are available or provide fallbacks when operating in constrained environments.
