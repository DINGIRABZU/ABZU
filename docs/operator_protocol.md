# Operator Protocol

Defines how operator commands are issued and validated across the system.

## Endpoint `/operator/command`

Sends a JSON payload describing the action to execute. Requests must use `POST` and include authentication headers.

## Roles and Permission Checks

Crown authorizes requests against `permissions.yml`. Only identities with the `operator` role may invoke this endpoint. Invalid or missing roles return a `403` response.

## Crown Relay to RAZAR

After validation Crown forwards the command to RAZAR's control loop. RAZAR executes the action and returns the result, which Crown relays back to the caller.

