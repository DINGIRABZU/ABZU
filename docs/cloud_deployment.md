# Cloud Deployment

This guide shows how to build the GPU enabled container and deploy Spiral OS on a Kubernetes cluster.

## Configure secrets

Copy `secrets.env.example` to `secrets.env` and fill out the variables required by the container and manifests:

- `HF_TOKEN` – Hugging Face token for model downloads
- `GITHUB_TOKEN` – optional token for scraping GitHub repositories
- `OPENAI_API_KEY` – OpenAI key if using OpenAI services
- `GLM_API_URL` – URL of the GLM service
- `GLM_API_KEY` – API key for the GLM service
- `GLM_SHELL_URL` – endpoint for the shell service
- `GLM_SHELL_KEY` – API key for the shell service
- `REFLECTION_INTERVAL` – interval in seconds for the reflection loop
- `CORPUS_PATH` – path to your text corpus
- `QNL_EMBED_MODEL` – embedding model name (default `all-MiniLM-L6-v2`)
- `QNL_MODEL_PATH` – directory containing QNL model weights
- `EMBED_MODEL_PATH` – optional path to the embedding model
- `VOICE_TONE_PATH` – directory of voice tone presets
- `VECTOR_DB_PATH` – location of the vector store
- `RETRAIN_THRESHOLD` – number of feedback items before retraining
- `VOICE_CONFIG_PATH` – override path to `voice_config.yaml`
- `EMOTION_STATE_PATH` – file used to persist emotion state
- `KIMI_K2_URL` – optional Kimi-K2 servant endpoint
- `LLM_ROTATION_PERIOD` – rotation period for active models
- `LLM_MAX_FAILURES` – allowed failures before rotation
- `ARCHETYPE_STATE` – starting archetype layer

## Build the container

Use the container spec `spiral_os_container.yaml` to build the image. The `codex` tool handles the build and automatically loads variables from `secrets.env`:

```bash
codex run spiral_os_container.yaml
```

This creates an image tagged `spiral_os:latest` and runs it locally with CUDA support.

Optionally tag and push the image to your own registry:

```bash
docker tag spiral_os:latest <registry>/spiral_os:latest
docker push <registry>/spiral_os:latest
```

## Deploy the manifests

After building (and optionally pushing) the container image, apply the Kubernetes manifests from the `k8s/` directory:

```bash
kubectl apply -f k8s/spiral_os_deployment.yaml
kubectl apply -f k8s/spiral_os_service.yaml
kubectl apply -f k8s/spiral_os_hpa.yaml
```

The deployment exposes port `8000` and defines readiness and liveness probes. Logs are written to `/workspace/logs/INANNA_AI.log` inside the pod.

Once running, open `web_console/index.html` to interact with the avatar. The page streams both audio and video via WebRTC.

For Vast.ai specific instructions, including the `scripts/vast_start.sh` launcher, see [VAST_DEPLOYMENT.md](VAST_DEPLOYMENT.md).
