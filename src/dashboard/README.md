# Dashboard

This package bundles Streamlit applications for monitoring and interacting with the system.

## Features
- **LLM Performance Metrics (`app.py`)** – visualise benchmark results and predict the optimal language model.
- **QNL Mixer (`qnl_mixer.py`)** – apply Quantum Narrative Language transformations to uploaded audio.
- **Reinforcement Learning Metrics (`rl_metrics.py`)** – chart user feedback metrics used during adaptive learning.
- **Usage Metrics (`usage.py`)** – display recent interactions and collected feedback entries.
- **System Monitor (`system_monitor.py`)** – command line tool for reporting CPU, memory and network usage.

## Configuration
- Launch any dashboard with `streamlit run src/dashboard/<module>.py`.
- `system_monitor.py` accepts:
  - `--watch` to continuously display statistics.
  - `--interval` to set the refresh rate when watching (default: `1.0`).
- `qnl_mixer.py` requires optional `librosa` and `soundfile` dependencies for audio processing.

## Screenshots
Example dashboard output:

![Metrics dashboard](./images/dashboard_example.png)

QNL Mixer spectrogram:

![QNL mixer](./images/qnl_mixer_example.png)
