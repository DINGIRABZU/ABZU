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
