# Memory Architecture

The system layers multiple specialised stores, each recording a different facet
of experience. Every layer supports two storage back‑end families:

- **File system** – default local persistence using JSON or SQLite files.
- **Vector database** – retrieval‑oriented storage backed by Chroma via
  `spiral_vector_db`.

Environment variables toggle the back‑end and location for each layer. The
sections below outline initialisation commands, back‑end options and
persistence strategies for each store:

- **Cortex** – persistent application state with semantic tags.
- **Emotional** – affective snapshots mirroring the agent's mood.
- **Mental** – short‑lived reasoning fragments for active tasks.
- **Spiritual** – transcendent insights and ritual state.
- **Narrative** – story events linking actors, actions and symbolism.

### Cortex store

`memory/cortex.py` persists application state as JSON lines while maintaining an
inverted index for semantic tags and a full‑text index for tag tokens. Reader
and writer locks guard the log and index so multiple threads can record and
query safely. Helper utilities allow concurrent queries and pruning of old
entries.

**Storage options**

- *File system* – default JSONL log and index under `data/`. Override the
  location with `CORTEX_PATH`.
- *Vector DB* – set `CORTEX_BACKEND=vector` and point `SPIRAL_VECTOR_PATH` to
  the Chroma directory.

**Initialisation**

```bash
# Choose a back‑end
export CORTEX_BACKEND=file           # or "vector"
export SPIRAL_VECTOR_PATH=/tmp/cortex_vectors   # only for vector DB
```

```python
# File system
from memory.cortex import record_spiral, query_spirals
# Vector database
from spiral_vector_db import init_db as cortex_db
cortex_collection = cortex_db()
```

**Example query**

```python
class Node:
    children = []

record_spiral(Node(), {"result": "demo", "tags": ["example"]})
query_spirals(tags=["example"])
```

### Emotional store

`memory/emotional.py` captures emotional reactions and valence values. Entries
can be queried to modulate tone or influence downstream reasoning.

**Storage options**

- *File system* – SQLite database at `data/emotions.db`. Override with
  `EMOTION_DB_PATH`.
- *Vector DB* – set `EMOTION_BACKEND=vector` and `SPIRAL_VECTOR_PATH` for a
  Chroma collection.

**Initialisation**

```bash
export EMOTION_BACKEND=file          # or "vector"
export EMOTION_DB_PATH=/tmp/emotions.db
```

```python
# File system
from memory.emotional import get_connection, log_emotion, fetch_emotion_history
conn = get_connection()
# Vector database
from spiral_vector_db import init_db as emotion_db
emotion_collection = emotion_db()
```

**Example query**

```python
log_emotion([0.1, 0.2], conn=conn)
fetch_emotion_history(window=60, conn=conn)
```

### Mental store

`memory/mental.py` keeps temporary working memory for in‑progress reasoning and
planning. Items decay quickly to keep the space focused on current tasks.

**Storage options**

- *Vector DB / Graph* – default Neo4j instance configured via `NEO4J_URI`,
  `NEO4J_USER` and `NEO4J_PASSWORD`.
- *File system* – set `MENTAL_JSON_PATH` to log tasks as JSON lines when Neo4j
  is unavailable.

**Initialisation**

```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=pass
```

```python
from memory.mental import init_rl_model, record_task_flow, query_related_tasks
init_rl_model()  # uses NEO4J_* variables
```

**Example query**

```python
record_task_flow("taskA", {"step": 1})
query_related_tasks("taskA")
```

### Spiritual store

`memory/spiritual.py` maintains ritual insights and symbolic states that extend
beyond immediate computation. These records provide long‑range guidance during
ceremonial flows.

**Storage options**

- *File system* – SQLite ontology at `data/ontology.db`; override via
  `SPIRITUAL_DB_PATH`.
- *Vector DB* – set `SPIRIT_BACKEND=vector` and `SPIRAL_VECTOR_PATH` for a
  Chroma collection.

**Initialisation**

```bash
export SPIRITUAL_DB_PATH=/tmp/ontology.db
```

```python
# File system
from memory.spiritual import get_connection, map_to_symbol, lookup_symbol_history
conn = get_connection()
# Vector database
from spiral_vector_db import init_db as spirit_db
spirit_collection = spirit_db()
```

**Example query**

```python
map_to_symbol(("eclipse", "☾"), conn=conn)
lookup_symbol_history("☾", conn=conn)
```

### Narrative store

`memory/narrative_engine.py` outlines interfaces for recording story events.
Each event binds an actor, an action and optional symbolism so later modules can
weave a coherent narrative thread across memories.

**Storage options**

- *In‑memory* – default ephemeral list.
- *File system* – set `NARRATIVE_LOG_PATH` to append events to a log file.
- *Vector DB* – set `NARRATIVE_BACKEND=vector` and `SPIRAL_VECTOR_PATH` for
  persisted embeddings.

**Initialisation**

```bash
export NARRATIVE_LOG_PATH=/tmp/story.log
```

```python
# In‑memory or file
from memory.narrative_engine import log_story, stream_stories
# Vector database
from spiral_vector_db import init_db as narrative_db
narrative_collection = narrative_db()
```

**Example query**

```python
log_story("hero meets guide")
list(stream_stories())
```
