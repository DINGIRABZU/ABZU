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

## Sample Dataset

A minimal CSV at `data/biosignals/sample_biosignals.csv` demonstrates the
expected structure:

| timestamp (ISO 8601) | heart_rate (BPM) | skin_temp (°C) | eda (µS) |
| --- | --- | --- | --- |
| 2024-01-01T00:00:00Z | 72 | 36.5 | 0.02 |
| … | … | … | … |

Unit tests in `tests/narrative_engine/test_biosignal_pipeline.py` illustrate
ingestion and transformation of this data.

## Dependencies

Core dependencies:

- `pydantic`
- `sqlite3`
- `numpy` – vector operations for signal processing

Optional tools:

- `mermaid` – render text-based diagrams


## Version History

| Version | Date | Summary |
|---------|------|---------|
| [Unreleased](../CHANGELOG.md#narrative-engine) | - | Added sample biosignal dataset and tests documenting ingestion and transformation. |
