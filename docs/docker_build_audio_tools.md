# Docker Image with Audio Tools

This project provides a Docker image that bundles the audio utilities **FFmpeg**
and **SoX**. The `Dockerfile` installs these binaries alongside the Python
dependencies.

## Build

```bash
docker build -t abzu .
```

## Validate

Run the environment check inside the container to confirm the binaries are
available:

```bash
docker run --rm abzu python - <<'PY'
import env_validation
env_validation.check_audio_binaries()
print("ffmpeg and sox available")
PY
```

The script exits without error when both tools are present.

