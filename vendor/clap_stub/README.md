# clap shim

This lightweight package exposes the CLAP processor and model from the
`transformers` library under the historical ``clap`` module name. Stage B
rehearsals relied on importing ``clap`` directly, but the upstream package is
unmaintained on modern Python versions. Installing this shim keeps the import
stable while delegating all heavy lifting to `transformers`.
