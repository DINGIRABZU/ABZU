# Python Legacy Audit

This audit lists known bugs and quirks in Python modules superseded by Rust crates. Each Rust implementation should verify these cases are handled or documented.

## crown_router.py

- Repeated memory evaluations were uncached, introducing latency until caching was implemented.
- Lacked tracing and telemetry; optional OpenTelemetry spans and broader instrumentation were added later.
- Initialization produced no boot-time metric, hindering performance diagnostics.

## kimicho.py

- Fallback logic originally shipped without tracing hooks or integration tests, making failures opaque.
- Early implementations omitted a K2 fallback path, leaving certain failure modes unhandled.

