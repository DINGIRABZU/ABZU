# Biosignal Acquisition Guidelines

This directory hosts anonymized biosignal samples used by the Nazarick Narrative System.

## Acquisition
- Capture heart rate, skin temperature, and electrodermal activity at **1 Hz** or higher.
- Timestamps must be recorded in **UTC** using ISO 8601 format.
- Ensure sensors are calibrated and synchronized before each session.

## Anonymization
- Strip all personal identifiers and replace session names with generic labels.
- Offset or obfuscate real-world dates if necessary.
- Review datasets for accidental metadata before sharing.

## File Format
- Provide data as CSV or JSON Lines files with the columns: `timestamp`, `heart_rate`, `skin_temp`, `eda`.
- Units: beats-per-minute (BPM) for heart rate, degrees Celsius for skin temperature, microSiemens for EDA.

## Schema
| column | type | unit |
| --- | --- | --- |
| `timestamp` | ISO 8601 UTC | - |
| `heart_rate` | float | BPM |
| `skin_temp` | float | °C |
| `eda` | float | µS |

## Ingestion
- Run `python scripts/ingest_biosignals.py` to transform rows into `StoryEvent` entries via `log_story`.
- Run `python scripts/ingest_biosignal_events.py` or `python scripts/ingest_biosignals_jsonl.py` to persist structured events with `log_event`.
- Tests in `tests/narrative_engine/` verify dataset conformity and transformation logic.

## Samples
- `sample_biosignals.csv`
- `sample_biosignals_alpha.csv`
- `sample_biosignals_beta.csv`
- `sample_biosignals_gamma.csv`
- `sample_biosignals_delta.csv`
- `sample_biosignals_epsilon.csv`
- `sample_biosignals_zeta.csv`
- `sample_biosignals_theta.csv`
- `sample_biosignals_iota.csv`
- `sample_biosignals_anonymized.jsonl`
