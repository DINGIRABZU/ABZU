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
- Provide data as CSV files with the columns: `timestamp`, `heart_rate`, `skin_temp`, `eda`.
- Units: beats-per-minute (BPM) for heart rate, degrees Celsius for skin temperature, microSiemens for EDA.

## Samples
- `sample_biosignals.csv`
- `sample_biosignals_alpha.csv`
- `sample_biosignals_beta.csv`

