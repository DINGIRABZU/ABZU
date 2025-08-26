# Memory Architecture

The system layers multiple specialised stores, each recording a different facet
of experience:

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

### Emotional store

`memory/emotional.py` captures emotional reactions and valence values. Entries
can be queried to modulate tone or influence downstream reasoning.

### Mental store

`memory/mental.py` keeps temporary working memory for in‑progress reasoning and
planning. Items decay quickly to keep the space focused on current tasks.

### Spiritual store

`memory/spiritual.py` maintains ritual insights and symbolic states that extend
beyond immediate computation. These records provide long‑range guidance during
ceremonial flows.

### Narrative store

`memory/narrative_engine.py` outlines interfaces for recording story events.
Each event binds an actor, an action and optional symbolism so later modules can
weave a coherent narrative thread across memories.
