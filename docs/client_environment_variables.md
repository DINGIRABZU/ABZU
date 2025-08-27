# Client environment variables

Clients interacting with the FastAPI server need several environment variables to authenticate requests.

- `GLM_COMMAND_TOKEN` – bearer token granting access to privileged routes such as `/glm-command`.
- `OPENWEBUI_USERNAME` and `OPENWEBUI_PASSWORD` – credentials for obtaining an access token from the `/token` endpoint. The returned token authorises `/openwebui-chat` requests.

Define these variables in your environment or within `secrets.env` before starting the server.
