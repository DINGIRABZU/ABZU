# OS Guardian Container

This guide covers running the `os_guardian` tools inside Docker.

## Environment variables

Set the following variables to configure the container:

- `DISPLAY` – display server address for GUI automation (e.g. `:0`).
- `YOLO_MODEL_PATH` – optional path to YOLOv8 weights for screen detection.
- `TESSDATA_PREFIX` – directory containing Tesseract language data.
- `HF_HOME` – optional location for cached Hugging Face models.
- `OG_POLICY` – permission mode for high-risk actions (`allow`, `ask`, `deny`).
- `OG_ALLOWED_APPS`, `OG_ALLOWED_DOMAINS`, `OG_ALLOWED_COMMANDS` – whitelists
  for the safety module.

Variables from `secrets.env` are also loaded by the helper script.

## Build and launch

Use the provided script to build the image and start the container:

```bash
bash scripts/setup_os_guardian.sh
```

The script mounts the repository at `/workspace`, forwards the host display using
`/tmp/.X11-unix` and publishes port `8000` for optional services. Additional
arguments are passed directly to `os-guardian` inside the container.

To run manually without the script:

```bash
docker build -f docker/os_guardian.Dockerfile -t os_guardian .
docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$(pwd)":/workspace \
  -p 8000:8000 \
  os_guardian
```
