# Vanna–Bana Pipeline

Vanna Data queries feed narrative generation by passing SQL results to the Bana engine, a fine-tuned Mistral 7B model. The engine creates multitrack stories—prose, audio cues, visual directives, and USD actions—which are persisted in memory for later retrieval.

```mermaid
flowchart LR
    OP[Operator] --> V[Vanna]
    V --> B[Bana (Mistral 7B)]
    B --> MT[Multitrack]
    MT --> P[Prose Track]
    MT --> A[Audio Track]
    MT --> VI[Visual Track]
    MT --> U[USD Track]
    MT --> M[Memory]
```

1. **Operator** issues a natural language query.
2. **Vanna** converts the query to SQL, executes it, and returns rows.
3. **Bana** interprets the rows with a Mistral 7B model, composing narrative events.
4. **Multitrack** output includes prose, audio cues, visual directives, and USD actions.
5. **Memory** stores the tracks and corresponding event logs.

See [Vanna Data Agent Usage](vanna_usage.md) for configuration details and [Bana Engine](bana_engine.md) for model architecture. The broader narrative flow is outlined in [Narrative System](narrative_system.md).
