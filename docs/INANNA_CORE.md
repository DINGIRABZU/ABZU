# INANNA Core Configuration

`config/INANNA_CORE.yaml` defines the default settings used by the Crown agent. Each option can be overridden by an environment variable, allowing different deployments without editing the file.

## Fields

- **`glm_api_url`** – Base URL for the GLM service. Override with `GLM_API_URL`.
- **`glm_api_key`** – API key for the GLM service. Override with `GLM_API_KEY`.
- **`model_path`** – Path to the GLM‑4.1V‑9B weights. Override with `MODEL_PATH`.
- **`memory_dir`** – Root directory containing the persistent memories. Override with `MEMORY_DIR`.
  It should contain two subdirectories:
  
  ```
  memory_dir/
  ├── vector_memory/
  └── chroma/
  ```
  `vector_memory/` stores embeddings written by `vector_memory.py` and
  `chroma/` holds the corpus store used by `corpus_memory`.
- **`servant_models`** – Optional HTTP endpoints for auxiliary models.
  Each key can be overridden individually:
  - `deepseek` – override with `DEEPSEEK_URL`.
  - `mistral` – override with `MISTRAL_URL`.
  - `kimi_k2` – override with `KIMI_K2_URL`.
  The values should point to endpoints that accept a JSON body `{"prompt": "..."}`
  and return the completion text.

## Example

```yaml
glm_api_url: https://api.example.com/glm41v_9b
glm_api_key: your-api-key
model_path: INANNA_AI/models/GLM-4.1V-9B
memory_dir: data/vector_memory
servant_models:
  deepseek: http://localhost:8002
  mistral: http://localhost:8003
  kimi_k2: http://localhost:8010
```

Environment variables with the same names as listed above override the
corresponding entries when `init_crown_agent.initialize_crown()` loads the file.
