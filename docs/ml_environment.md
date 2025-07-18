# ML Environment Setup

This guide explains how to create an isolated Python environment and start Jupyter notebooks for experimenting with Spiral OS.

## Virtualenv

Create a `venv` directory and install the requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r dev-requirements.txt
```

## Conda

Alternatively use Conda:

```bash
conda create -n spiral python=3.10
conda activate spiral
pip install -r requirements.txt -r dev-requirements.txt
```

## Launching Jupyter

With the environment active run:

```bash
jupyter lab
```

The notebooks will use the packages installed in the current environment.
