# Deployment

This guide covers building versioned images and deploying them using Kubernetes or a serverless platform. For vision module dependencies and GPU sizing, see the [Vision System](vision_system.md) guide.

## Build and publish images

1. Set the desired version:
   ```bash
   export APP_VERSION=1.0.0
   ```
2. Build the production image and tag it with the version:
   ```bash
   docker compose -f docker-compose.production.yml build
   ```
3. Publish the image to your registry:
   ```bash
   docker push registry.example.com/abzu:${APP_VERSION}
   ```

## OpenWebUI

1. Define the FastAPI endpoint that OpenWebUI should use:
   ```bash
   export FASTAPI_BASE_URL=http://localhost:8000
   ```
2. Launch the interface:
   ```bash
   docker compose -f docker-compose.openwebui.yml up
   ```
   The UI is available at http://localhost:3000.

## Kubernetes

Reference manifests live in `deployment/kubernetes`. Apply them with:

```bash
kubectl apply -f deployment/kubernetes/
```

## Serverless

Sample function definitions reside in `deployment/serverless`. Deploy using your provider's tooling, e.g.:

```bash
sls deploy
```
