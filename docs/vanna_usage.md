# Vanna Data Agent Usage

The `vanna_data` agent translates natural language prompts into SQL queries using the [Vanna](https://github.com/vanna-ai/vanna) library. Query results are stored in mental memory while narrative summaries are appended to `data/narrative.log`.

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
