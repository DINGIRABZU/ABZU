# Memory Architecture

The system layers multiple specialised stores, each recording a different facet
of experience. Each section below shows how to initialise the store and run a
basic query:

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

**Initialisation**

```python
from memory.cortex import record_spiral, query_spirals
# Files are created on first use; no explicit setup is required.
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

**Initialisation**

```python
from memory.emotional import get_connection, log_emotion, fetch_emotion_history
conn = get_connection()
```

**Example query**

```python
log_emotion([0.1, 0.2], conn=conn)
fetch_emotion_history(window=60, conn=conn)
```

### Mental store

`memory/mental.py` keeps temporary working memory for in‑progress reasoning and
planning. Items decay quickly to keep the space focused on current tasks.

**Initialisation**

```python
from memory.mental import init_rl_model, record_task_flow, query_related_tasks
init_rl_model()
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

**Initialisation**

```python
from memory.spiritual import get_connection, map_to_symbol, lookup_symbol_history
conn = get_connection()
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

**Initialisation**

```python
from memory.narrative_engine import log_story, stream_stories
```

**Example query**

```python
log_story("hero meets guide")
list(stream_stories())
```
