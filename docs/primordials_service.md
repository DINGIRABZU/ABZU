# Primordials Service

The Primordials service hosts the DeepSeek-V3 language model for internal orchestration tasks. It exposes HTTP endpoints for invoking the model, requesting inspirational prompts, and reporting service health.

See the [component index entry](../component_index.json) for metadata on this service.

## Deployment

DeepSeek-V3 runs within an isolated container and loads weights on startup. The service requires access to GPU resources and the model checkpoints provided by the deployment pipeline.

## API Endpoints

### `POST /invoke`
Invoke DeepSeek-V3 with structured messages.

**Request schema**
```json
{
  "messages": [
    {"role": "system", "content": "instruction"},
    {"role": "user", "content": "question"}
  ],
  "stream": false
}
```

**Response schema**
```json
{
  "output": "model reply",
  "model": "DeepSeek-V3"
}
```

### `POST /inspire`
Ask the model for creative guidance.

**Request schema**
```json
{
  "prompt": "seed idea",
  "max_ideas": 3
}
```

**Response schema**
```json
{
  "ideas": ["first", "second", "third"]
}
```

### `GET /health`
Health probe returning readiness status.

**Response schema**
```json
{
  "status": "ok"
}
```

## Related Documents
- [Key Documents](KEY_DOCUMENTS.md)
