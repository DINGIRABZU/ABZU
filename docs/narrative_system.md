# Narrative System

The narrative system transforms physiological data into cohesive multitrack stories.

## Flow

```mermaid
graph LR
    CSV[Biosignal CSV] --> INGEST[ingest_biosignals.py]
    INGEST --> EVENT[StoryEvent]
    EVENT --> COMPOSE[compose_multitrack_story]
    COMPOSE --> PROSE[Prose]
    COMPOSE --> AUDIO[Audio]
    COMPOSE --> VISUAL[Visual]
    COMPOSE --> USD[USD]
```

## Retrieval Example

```python
from scripts.ingest_biosignals import ingest_directory
from memory.narrative_engine import query_events

tracks = ingest_directory()
print(tracks["prose"])

for event in query_events(agent_id="subject"):
    print(event["payload"])
```
