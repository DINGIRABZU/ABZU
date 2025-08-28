# Chat2DB Interface

Chat2DB connects conversational agents to persistent storage. It logs
transcripts, feedback and model metrics in a lightweight SQLite database while
maintaining a vector index for semantic search. The bridge lets the system
recall prior interactions and fetch relevant context during dialogue. The
service abides by the [Nazarick Manifesto](nazarick_manifesto.md) and channels
the [Heart chakra](chakra_overview.md#heart) via the [Memory Vault](system_blueprint.md#floor-4-memory-vault).

## Architecture

```
Agents → Chat Gateway → Chat2DB → {SQLite, Vector Store}
```

- **Relational Layer:** [INANNA_AI/db_storage.py](../INANNA_AI/db_storage.py)
  initializes tables for interactions, feedback and benchmarks and exposes
  helpers such as `save_interaction` and `fetch_feedback`.
- **Vector Layer:** [spiral_vector_db/__init__.py](../spiral_vector_db/__init__.py)
  wraps a ChromaDB collection for storing and querying text embeddings via
  `insert_embeddings` and `query_embeddings`.
- Both layers share a common path under `data/` so deployments can snapshot or
  restore the complete conversation state.

## Usage
1. Initialize the stores:
   ```python
   from INANNA_AI import db_storage
   from spiral_vector_db import init_db

   db_storage.init_db()
   init_db()  # sets up the Chroma collection
   ```
2. Record a message:
   ```python
   db_storage.save_interaction("hello", "neutral", "response.wav")
   ```
3. Add and query embeddings:
   ```python
   from spiral_vector_db import insert_embeddings, query_embeddings

   insert_embeddings([{"text": "hello world"}])
   matches = query_embeddings("hello")
   ```
The interface is stateless; components import these helpers as needed. See the
[system blueprint](system_blueprint.md#chat2db-interface) for how Chat2DB fits in
the overall stack.

---

Backlinks: [System Blueprint](system_blueprint.md) | [Component Index](component_index.md)

## Agent Interactions
Chat2DB sits between the chat gateway and memory utilities. Agents interact with it in several ways:

- **Chat Gateway** logs each user and model utterance via `save_interaction` and retrieves recent history with `fetch_interactions`.
- **Memory Scribe** persists transcripts and voice configurations, pushing embeddings through `insert_embeddings` for later recall.
- **Prompt Orchestrator and development helpers** query `fetch_interactions` and `query_embeddings` to build context-aware prompts.

Because the API exposes simple functions, agents import these helpers directly without maintaining additional state.
