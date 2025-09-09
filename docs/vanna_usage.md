# Vanna Data Agent Usage

The `vanna_data` agent translates natural language prompts into SQL queries using the [Vanna](https://github.com/vanna-ai/vanna) library. Query results are stored in mental memory while narrative summaries are appended to `data/narrative.log`.

For the end-to-end storytelling flow, see [Vanna–Bana Pipeline](vanna_bana_pipeline.md).

## Setup

1. `pip install vanna`
2. Configure credentials and database connection:

   ```python
   import vanna

   vanna.set_api_key("YOUR_API_KEY")
   vanna.set_model("your-model")
   vanna.connect_to_sqlite("my.db")  # or another supported backend
   ```

If the library is missing or the connection is not established, `agents.vanna_data`
logs a warning and raises a runtime error when invoked.

## Training

Before answering questions Vanna should learn your schema:

```python
from pathlib import Path

sql_statements = Path("schema.sql").read_text()
vanna.train(sql=sql_statements)
```

Additional domain examples can be supplied via `vanna.train(document=...)`
to improve natural language understanding.

## Basic Example

```python
import vanna
from agents.vanna_data import query_db

# Configure Vanna with your API key, model, and database connection
vanna.set_api_key("YOUR_API_KEY")
vanna.set_model("your-model")
vanna.connect_to_sqlite("my.db")

rows = query_db("How many users signed up last week?")
print(rows)
```

The call stores the raw rows in Neo4j-backed mental memory and records a summary event in narrative memory for later storytelling.
## Narrative Export

Query results can be streamed into Bana's narrative engine to generate multitrack stories. Bana converts each row into a `StoryEvent` and emits prose, audio, visual, and USD operations. The `usd` track follows the schema described in [Narrative System](narrative_system.md).

```python
from agents.vanna_data import query_db
from memory.narrative_engine import StoryEvent, compose_multitrack_story

rows = query_db("SELECT hero, action FROM quests")

events = [StoryEvent(actor=r["hero"], action=r["action"]) for r in rows]
usd_track = compose_multitrack_story(events)["usd"]
```

`usd_track` contains the structured USD operations that downstream tools consume to build scenes.
