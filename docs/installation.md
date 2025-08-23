# Installation

Set up the project either with Conda or Docker. Both methods run the
bootstrap script, which verifies the Python version, installs FAISS and
SQLite support if missing, and checks required environment variables.

## Conda

```bash
conda env create -f environment.yml
conda run -n abzu python scripts/bootstrap.py
```

On Apple Silicon the `faiss-cpu` wheel comes from the `conda-forge` channel.
Linux systems may require `libsqlite3` development headers to build the
SQLite module.

## Docker

```bash
docker build -t abzu -f docker/Dockerfile .
docker run -it abzu
```

Pass environment variables with `--env-file` or `-e` as needed for your
platform.
