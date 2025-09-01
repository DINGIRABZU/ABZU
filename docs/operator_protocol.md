# Operator Protocol

Outlines the operator-facing interfaces used to control the Crown and RAZAR stack.

## `/operator/command`
Sends a JSON body with an `action` field and optional `parameters`. Crown forwards the request to RAZAR and returns the resulting status and any output.

## `/operator/upload`
Accepts multipart form data containing one or more `files` parts and a `metadata` field. The service stores the files and merges their paths into the provided metadata before relaying everything to RAZAR.

## Authentication
All operator requests require a Bearer token in the `Authorization` header. Tokens are JWTs issued by Crown and must include the `operator` role.

## Escalation
1. RAZAR handles normal commands and uploads.
2. If RAZAR cannot fulfil a request, it forwards the context to Crown for arbitration.
3. Crown may escalate to a human operator for confirmation or rejection. Every escalation is recorded in the mission-brief log.
