# RAZAR Agent

RAZAR serves as the startup orchestrator for Nazarick, acting as "service 0". It prepares the runtime before any other agent activates.

## Component Priority

RAZAR ranks downstream components on a 1‑5 scale:

1. **Critical** – mandatory for boot.
2. **Required** – core functionality.
3. **Important** – enhances core but can start later.
4. **Optional** – noncritical utilities.
5. **Experimental** – development or diagnostic helpers.

This classification guides launch order and restart policy.

## Virtual Environment Management and Restart Logic

RAZAR ensures a clean Python virtual environment:

- creates or updates the `venv` at startup,
- verifies required packages against `requirements.txt`,
- injects paths into `PYTHONPATH` for launched services.

If a component exits or the environment hash changes, RAZAR restarts the affected process. Repeated failures trigger a full environment rebuild and orchestrator restart.

