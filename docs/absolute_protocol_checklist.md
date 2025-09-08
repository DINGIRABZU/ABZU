# Absolute Protocol Release Checklist

Complete this checklist before tagging a release. Mark each item with `[x]` once satisfied.

- [ ] `docs/INDEX.md` regenerated and committed
- [ ] All tests pass (`pytest`)
- [ ] Code coverage meets project threshold
- [ ] Run `python scripts/check_connectors.py` and confirm connector protocol and heartbeat metadata are documented
- [ ] `environment.yml` and `environment.gpu.yml` unchanged
