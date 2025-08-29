# Operator Protocol

Defines how operator commands and uploads are issued and validated across the system.

## Endpoint `/operator/command`

Sends a JSON payload describing the action to execute. Requests must use `POST` and include authentication headers.

## Endpoint `/operator/upload`

Uploads one or more files using `multipart/form-data`. Each request must include a `files` field and may include an optional `metadata` field containing JSON. Crown saves files under `uploads/` and forwards the metadata to RAZAR.

## Roles and Permission Checks

Crown authorizes requests against `permissions.yml`. Only identities with the `operator` role may invoke this endpoint. Invalid or missing roles return a `403` response.

## Authentication and Rate Limits

All operator endpoints require `Authorization` headers. Crown enforces a rate limit of 60 command requests and 5 upload requests per minute per operator.

## Crown Relay to RAZAR

After validation Crown forwards the command to RAZAR's control loop. RAZAR executes the action and returns the result, which Crown relays back to the caller.

## Escalation Path

RAZAR and Crown follow the [Co-creation Escalation](co_creation_escalation.md) guide when automated recovery fails. It defines when RAZAR requests Crown assistance, when Crown alerts the operator, and how each step is logged.
