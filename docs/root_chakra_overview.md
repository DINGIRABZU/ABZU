# Root Chakra Overview

The Root layer provides the foundation for hardware and network access. Its primary modules focus on serving requests, monitoring traffic and reporting basic system status.

## `server.py`

`server.py` exposes a small FastAPI application. It includes `/health` and `/ready` endpoints for container probes, `/glm-command` to forward shell commands to the GLM service, and `/avatar-frame` which streams video frames as base64 images. The `/glm-command` route requires the `GLM_COMMAND_TOKEN` environment variable to authorise requests.

## `INANNA_AI.network_utils`

This package offers command line helpers for packet capture and traffic analysis. Use the module directly with `python -m INANNA_AI.network_utils` and one of the subcommands:

- `capture <iface>` – write a short capture using scapy.
- `analyze <pcap>` – print a protocol summary and save a log.
- `schedule <iface>` – run captures periodically.

Configuration values such as the log directory and default pcap path are read from `INANNA_AI_AGENT/network_utils_config.json` when present.

## `system_monitor.py`

`system_monitor` collects CPU, memory and network statistics via `psutil`. Run it with `--watch` to continuously print JSON formatted data or without arguments to output a single sample.

## Environment variables

Several variables influence the Root layer:

- `GLM_COMMAND_TOKEN` – authorises `/glm-command` requests.
- `WEB_CONSOLE_API_URL` – enables WebRTC connectors when present.
- `GLM_API_URL` and `GLM_API_KEY` – endpoint and key for the GLM service.
- `HF_TOKEN` – Hugging Face token for model downloads.
- `ARCHETYPE_STATE` – initial personality layer loaded by `start_spiral_os.py`.
- `REFLECTION_INTERVAL` – default delay between reflection cycles.

These variables are typically defined in `secrets.env` or passed in the environment when launching `start_spiral_os.py`.
