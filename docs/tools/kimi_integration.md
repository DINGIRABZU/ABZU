# Kimi Integration

Opencode can delegate code generation to the Kimi-K2 model when the service is available.

1. Launch a Kimi-K2 service and note its URL.
2. Set environment variables:
   - `KIMI_K2_URL` – endpoint for the Kimi-2 service.
   - `OPENCODE_BACKEND=kimi` – route Opencode requests through Kimi.
3. Use `tools.opencode_client.complete` for code-generation tasks; it will call Kimi when configured.

Kimi-2 excels at reasoning about code and provides a lightweight backend for Opencode-driven development.
