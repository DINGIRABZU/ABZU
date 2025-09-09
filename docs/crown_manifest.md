# CROWN Manifest

The **CROWN** agent runs the GLM-4.1V-9B model and acts as the root layer of Spiral OS. It holds the highest permission level and can rewrite memory entries or initiate ritual sequences when commanded.

## Relationship to other layers

The archetypal layers described in [spiritual_architecture.md](spiritual_architecture.md) present personas such as Nigredo and Albedo. The CROWN coordinates these layers, dispatching prompts to each personality and receiving their responses. By updating the vector memory store the CROWN influences how future interactions surface across the layers.

For the mission brief exchange and servant routing sequence see [Mission Brief Exchange & Servant Routing](mission_brief_exchange.md).

## Console connection

Commands typed into the Crown Console reach the agent through `crown_prompt_orchestrator.py`. The CROWN interprets these requests, sends them to GLM-4.1V-9B and triggers ritual logic in `state_transition_engine.py` when specific phrases appear.

Memory mutations happen through `vector_memory.py` and are authorised only when the CROWN is active. This ensures a single authority controls persistent memories and the rituals that can reshape them.

### Command-line usage

`crown_prompt_orchestrator.py` exposes a CLI that processes a single message with optional model configuration. After installing the package it can be invoked via the `crown-prompt` command:

```bash
crown-prompt "hello world" --model path.to.CustomModel
```

Without installation the module may be executed directly:

```bash
python -m crown_prompt_orchestrator "hello world"
```

## Emotion model mapping

The orchestrator exposes a lookup table called `_EMOTION_MODEL_MATRIX` which matches a detected emotion to the LLM best suited to respond. This mapping is tested to guarantee consistent routing behaviour.

| Emotion | Preferred model |
|---------|-----------------|
| joy     | deepseek        |
| excited | deepseek        |
| stress  | mistral         |
| fear    | mistral         |
| sad     | mistral         |
| calm    | glm             |
| neutral | glm             |

The selected model also determines the text-to-speech backend used when voice output is enabled. `decide_expression_options()` inspects recent vector memory records to choose between Google TTS, Bark or Coqui. Frequent entries of the same emotion are logged as `routing_decision` records and gradually bias future model selection toward the most successful choice.

For a neutral summary of the router and related modules, see [architecture_overview.md](architecture_overview.md).

## Key Scripts

- `start_spiral_os.py` launches the Spiral OS initialization sequence and checks required environment configuration.
- `init_crown_agent.py` prepares the Crown agent, servants and optional vector memory.
- `crown_router.py` routes model and expression decisions using recent emotional context.
- `crown_decider.py` selects language models and expressive options based on heuristic rules.

## Endpoint configuration

The GLM endpoint and optional servants are configured through environment variables:

| Variable         | Purpose                                         |
|------------------|-------------------------------------------------|
| `GLM_API_URL`    | Base URL of the primary GLM endpoint            |
| `GLM_API_KEY`    | Bearer token for authenticated GLM access       |
| `DEEPSEEK_URL`   | Optional DeepSeek servant endpoint              |
| `MISTRAL_URL`    | Optional Mistral servant endpoint               |
| `KIMI_K2_URL`    | Optional Kimi‑K2 servant endpoint               |
| `OPENCODE_URL`   | Optional OpenCode control endpoint              |
| `SERVANT_MODELS` | Comma‑separated `name=url` pairs for servants   |

### Runtime registration

```mermaid
flowchart LR
    subgraph Env
        G[GLM_API_URL]
        D[DEEPSEEK_URL]
        M[MISTRAL_URL]
        K[KIMI_K2_URL]
        O[OPENCODE_URL]
        S[SERVANT_MODELS]
    end
    Env -->|initialize_crown()| R[Registry]
    R --> GLM[GLM core]
    R --> DS[DeepSeek]
    R --> MS[Mistral]
    R --> K2[Kimi K2]
    R --> OC[OpenCode]
```

`init_crown_agent.initialize_crown()` reads these settings and registers any
servant endpoints before performing startup checks. The Crown agent requires the
`requests` package and aborts immediately if it is missing. During startup each
registered endpoint is contacted at `/health`; a failing response stops
initialization so misconfiguration is detected early.

## Quickstart

```python
import os
import requests
from init_crown_agent import initialize_crown

os.environ.update({
    "GLM_API_URL": "http://localhost:8000",
    "SERVANT_MODELS": (
        "deepseek=http://localhost:8002,"
        "mistral=http://localhost:8003,"
        "kimi_k2=http://localhost:8010"
    ),
})

crown = initialize_crown()

for url in [os.environ["GLM_API_URL"], *crown.servants.values()]:
    requests.get(f"{url}/health").raise_for_status()
```

## Health check

During startup the Crown agent calls `/health` on the configured GLM endpoint
and each servant model. A failing request raises `RuntimeError` and aborts
initialization. The same health endpoint is exposed by the Crown server and can
be queried manually:

```bash
curl http://localhost:8000/health
```

The command returns `{"status": "alive"}` when the service is ready to accept
requests.

## Servant isolation

Servant models run as independent HTTP services. The Crown calls each endpoint
directly and never shares state between servants. To add a new servant, expose
its URL via `SERVANT_MODELS` or a dedicated `<NAME>_URL` variable and ensure its
`/health` check responds before letting operators interact with it. This
registration flow keeps untrusted models sandboxed and prevents them from
interfering with each other or the core GLM.
