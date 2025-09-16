# Environment Setup

## Dependency locking

Regenerate `requirements.lock` when `requirements.txt` or `dev-requirements.txt` change:

```bash
pip-compile --allow-unsafe --generate-hashes \
  --output-file=requirements.lock dev-requirements.txt requirements.txt
```

## Local installation

Install the pinned dependencies and register the project in editable mode so tools such as `task_profiling.py` resolve the `core` package:

```bash
pip install -r requirements.lock
pip install -e .
```

## Tracing stack

Install the optional tracing dependencies to enable OpenTelemetry
instrumentation:

```bash
pip install .[tracing]
```

The tracing system uses a factory that selects providers based on the
``TRACE_PROVIDER`` environment variable. ``opentelemetry`` remains the default
when the package is installed and yields spans via ``trace.get_tracer``. Set
``TRACE_PROVIDER`` to switch providers:

```bash
export TRACE_PROVIDER=opentelemetry  # use OpenTelemetry
export TRACE_PROVIDER=noop           # disable tracing
export TRACE_PROVIDER=my_pkg.tracing:factory  # custom entry point
```

These packages are optional; configure your collector or export endpoint as
needed to capture spans during development.

## Conda environments

### CPU

Create a CPU-only environment with the pinned versions in `environment.yml`:

```bash
conda env create -f environment.yml
conda activate abzu
```

### GPU

For systems with NVIDIA GPUs and CUDA 12.1 support, use `environment.gpu.yml`:

```bash
conda env create -f environment.gpu.yml
conda activate abzu-gpu
```

## Docker images

### CPU build

```bash
docker build -f docker/Dockerfile.cpu -t abzu-cpu .
```

### GPU build

```bash
docker build -f docker/Dockerfile.gpu -t abzu-gpu .
```

## Hardware requirements

- **CPU environment:** 4+ CPU cores, 8 GB RAM, 20 GB free disk space.
- **GPU environment:** NVIDIA GPU with compute capability ≥7.0, CUDA 12.1‑compatible drivers, and 12 GB+ VRAM.

Run `scripts/check_requirements.sh` after installation to verify the setup.

## rStar service

Expose the `rStar` patch API by setting its endpoint and access token:

```bash
export RSTAR_ENDPOINT=http://localhost:8000/patch
export RSTAR_API_KEY=your_token
```
