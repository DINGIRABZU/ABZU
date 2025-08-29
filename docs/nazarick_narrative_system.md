# Nazarick Narrative System

The Nazarick Narrative System turns raw biosensor readings into adaptive story cues for the tomb.

## Architecture
Sensors feed a biosignal processing layer that emits structured events for the narrative engine. The engine records these events through the scribe and updates personas in the registry for downstream agents.

```mermaid
flowchart LR
    Sensors --> Normalization --> "Feature Extraction" --> "Event Generator" --> "Narrative Engine" --> Outputs
```

## Biosignal Pipeline
1. **Sensors** – EEG, heart-rate, and motion devices stream data.
2. **Normalization** – signals are cleaned and aligned on a shared clock.
3. **Feature Extraction** – metrics such as pulse variability or gaze direction are derived.
4. **Event Generator** – extracted features translate into narrative events consumed by the scribe.
5. **Narrative Engine** – generates context-aware story elements.

## Dependencies

Core dependencies:

- `pydantic`
- `sqlite3`
- `numpy` – vector operations for signal processing

Optional tools:

- `mermaid` – render text-based diagrams

