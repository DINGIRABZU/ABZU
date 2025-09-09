# Operator Quickstart

Minimal steps to launch ABZU's Operator API and Arcade UI.

## Minimal Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.lock
   ```
2. **Prepare a token**
   ```bash
   cp secrets.env.template secrets.env
   echo "OPERATOR_TOKEN=test-token" >> secrets.env
   ```
3. **Start the local stack**
   ```bash
   bash scripts/start_local.sh
   ```
   The Operator API comes up on `http://localhost:8000` and the Arcade UI opens in your browser.
   Restart the UI anytime with `npm start --prefix web_console`.

## Authentication

The Operator API and Arcade UI expect a bearer token.

```bash
export OPERATOR_API_URL="http://localhost:8000"
export OPERATOR_TOKEN="test-token"
```

Command‑line requests use the same token:

```bash
curl -H "Authorization: Bearer $OPERATOR_TOKEN" $OPERATOR_API_URL/status
```

## Arcade UI Walkthrough

### Memory Scan
1. In the Arcade UI, open the **Memory Scan** panel.
2. Enter a term such as `vision` and press **Scan**.
3. Results from `/memory/query` appear in the log panel.

### Run a Command
1. Open the **Console** input at the bottom of the UI.
2. Type `status` and press **Send** to invoke `/status`.
3. For a system action, enter `ignite` to trigger `/start_ignition` and watch updates stream in.

## Next Steps

- See [operator_console.md](operator_console.md) for the full interface reference.
- Review [operator_protocol.md](operator_protocol.md) for rules governing operator actions.
- For complete environment configuration, consult [setup.md](setup.md).
