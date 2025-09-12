# MCP Connectors

Assessment of tools and services for Model Context Protocol integration.

## Contribution Guidelines

Any pull request adding a connector must append its specification here with
heartbeat and health details.

## Decision Matrix

| Tool/Service | MCP Ready | Integration Effort | Notes |
| --- | --- | --- | --- |
| Slack Events API | Partial | Medium | Webhook interface fits MCP event model; requires auth wrapper. |
| GitHub Actions | No | High | Needs job runner bridge and context mapping to MCP schemas. |
| Notion API | Partial | Medium | Structured blocks align with MCP context; subject to rate limits. |
| LangChain | Yes | Low | Community adapter exposes chains over MCP. |
| Open WebUI | Yes | Low | Bundled MCP bridge for local models. |

## Integration Roadmap

1. Prototype Slack and Open WebUI connectors with heartbeat telemetry.
2. Add Notion and LangChain adapters, validating context registration.
3. Expand to GitHub Actions and publish reference implementations.

Backlinks: [MCP Gateway Overview](mcp_overview.md)
