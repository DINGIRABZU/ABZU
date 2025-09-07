# MCP Gateway Overview

The MCP gateway bridges existing FastAPI services with the Model Context Protocol.
It exposes context registration and model invocation over MCP while continuing to
serve the legacy HTTP routes.

## Configuration
- `config/mcp.toml` defines model paths, rate limits, and API keys.

## Endpoints
- **`/context/register`** – register conversation context.
- **`/model/invoke`** – invoke a configured model.

## Version History
- 2025-10-??: Initial version.

Backlinks: [Blueprint Spine](blueprint_spine.md)
