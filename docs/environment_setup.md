# Environment Setup

## Dependency locking

Regenerate `requirements.lock` when `requirements.txt` or `dev-requirements.txt`
change:

```bash
pip-compile --allow-unsafe --generate-hashes \
  --output-file=requirements.lock dev-requirements.txt requirements.txt
```

## Local installation

Install the pinned dependencies and register the project in editable mode so
tools such as `task_profiling.py` resolve the `core` package:

```bash
pip install -r requirements.lock
pip install -e .
```

## Docker image

The Dockerfile uses `requirements.lock` and installs the project in editable
mode. Build the container with:

```bash
docker build -t abzu .
```
