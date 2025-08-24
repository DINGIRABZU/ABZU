# Reproducibility

This project relies on [DVC](https://dvc.org) for data and model versioning and on `docker compose` for repeatable environments.

## DVC pipeline

Rebuild the data pipeline and refresh derived artifacts with:

```bash
dvc repro
```

The command traverses `dvc.yaml`, executing the steps needed to regenerate outdated stages.

## Docker compose environment

Spin up a consistent runtime using the provided compose file:

```bash
docker compose up --build
```

The `--build` flag ensures images reflect the current codebase. Add `-d` to run services in the background.

Together these tools keep experiments and deployments reproducible across machines.
