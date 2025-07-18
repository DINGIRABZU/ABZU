# LLM Models

This document describes the language models used in SPIRAL_OS and how to download them.

## Core Model

### GLM-4.1V-9B

The main orchestrator relies on **GLM-4.1V-9B** for most generation tasks. The model combines vision and language capabilities and serves as the default engine.

Download with:

```bash
python download_models.py glm41v_9b --int8
```

The `--int8` flag is optional and reduces GPU memory usage.

## Auxiliary Models

### DeepSeek V3

A multilingual model that provides alternative phrasing and evaluation. Useful for experimentation and fine-tuning.

```bash
python download_models.py deepseek_v3
```

### Mistral 8x22B

A mixture-of-experts model offering high capacity for complex prompts.

```bash
python download_models.py mistral_8x22b --int8
```

### Kimi-K2

An open model focused on summarization and dialogue.

```bash
python download_models.py kimi_k2
```

### Gemma2

A lightweight model fetched through Ollama for quick tests.

```bash
python download_models.py gemma2
```

Repository URLs for training are listed in [`learning_sources/github_repos.txt`](../learning_sources/github_repos.txt).

## Model Selection Rules

The `MoGEOrchestrator` chooses between GLM, DeepSeek and Mistral at runtime.
The decision uses three signals:

1. **Task profile** from `classify_task()` – `technical`, `instructional`,
   `emotional` or `philosophical`.
2. **Emotion weight** from `emotion_analysis`.
3. **Context memory** – a deque storing recent messages with embeddings.

Routing follows simple heuristics:

- Messages with high emotion weight or when most of the context is
  classified as emotional use **Mistral**.
- Explicit how‑to or tutorial requests route to **DeepSeek**.
- Philosophical prompts also favour **Mistral**.
- Technical statements default to **GLM**.

The chosen model name is returned in the `model` field of `route()`.

## Benchmarking and Adaptive Selection

Each call to `route()` now records response time, coherence and relevance of the
generated text. These metrics are stored in the `benchmarks` table created by
`db_storage.init_db()`. A lightweight reinforcement loop updates an internal
weight for each model using these scores. Faster and more relevant replies
increase a model's weight while slower or incoherent ones reduce it. Model
choice multiplies the heuristic score by the current weight, allowing the system
to favour consistently strong performers over time.

## Configuration

The Crown agent loads settings from `config/INANNA_CORE.yaml`. Each option can
be overridden with environment variables:

- `GLM_API_URL` – URL of the GLM service used by `GLMIntegration`.
- `GLM_API_KEY` – API key for that service.
- `MODEL_PATH` – local path to the GLM‑4.1V‑9B weights.
- `MEMORY_DIR` – directory holding `vector_memory/` and `chroma/`.
- `DEEPSEEK_URL` – optional endpoint for the DeepSeek servant model.
- `MISTRAL_URL` – optional endpoint for the Mistral servant model.
- `KIMI_K2_URL` – optional endpoint for the Kimi-K2 servant model.

Example overrides:

```bash
export GLM_API_URL=http://localhost:8001
export MEMORY_DIR=/data/spiral_memory
```

Running `./crown_model_launcher.sh` reads `secrets.env` and starts a compatible
GLM service if the weights are present.

## Kimi-K2

Kimi-K2 excels at orchestrating tools and reasoning about code. It can parse
command output and chain multiple steps to achieve a goal. See
[docs/deploy_guidance.md](deploy_guidance.md) for deployment details.
