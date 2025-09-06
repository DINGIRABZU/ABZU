# World Bootstrap

Initialize ABZU's world by preparing memory layers, starting Crown services, and
loading agent profiles.

## Prerequisites

- Python 3.10+
- Environment tokens:
  - `HF_TOKEN` for model downloads and tokenizer access
  - `GLM_API_KEY` for Crown language model endpoints
- Optional `SERVANT_MODELS` for additional servant URLs

## Usage

```bash
abzu-bootstrap-world
```

The command:

1. Seeds file-backed cortex, emotional, mental, spiritual, and narrative layers
2. Initializes Crown using `config/crown.yml`
3. Launches agents listed in `agents/nazarick/agent_registry.json`

## Optional Services

- **Vector memory** – requires the `faiss` package; skipped if absent
- **Mental layer** – uses Neo4j when available, otherwise a JSONL fallback
- **Servant models** – custom endpoints from `SERVANT_MODELS`

## Updating Models and Tokenizers

Service parameters are declared per world in `worlds/services.yaml`. Adjust the
`model` and `tokenizer` entries for your world, then rerun
`abzu-bootstrap-world`. The bootstrap process validates the manifest and warns
when a configured service is missing.

## Repair Metadata

Remote repair attempts, the patches applied, and the resulting component hashes
are tracked in `worlds/config_registry`. When exporting world configuration, the
`remote_attempts` field counts how many AI patches were applied per component,
`patches` records each patch alongside its final digest, and
`component_hashes` stores each component's current hash. Import these fields
into newly cloned worlds to reproduce a repaired state.

## Exporting Configuration

Use the `abzu-world-export` command to capture the current world's metadata for
bootstrapping elsewhere:

```bash
abzu-world-export world.json
```

The command writes `world.json` (or your chosen path) containing layer, agent,
service, and repair data, including patches and component hashes.

