# Albedo Personality Layer

The **Albedo** layer introduces a stateful persona that drives responses through a remote GLM (Generative Language Model). All related modules live under `INANNA_AI/personality_layers/albedo`.

## Project structure

- `__init__.py` – exposes `AlbedoPersonality` used by the orchestrator.
- `alchemical_persona.py` – weighted state machine with `detect_state_trigger()`.
- `state_contexts.py` – prompt templates applied for each state.
- `glm_integration.py` – `GLMIntegration` class for HTTP requests.

`AlbedoPersonality` calls `detect_state_trigger()` to extract entities and emotional cues, builds a state specific prompt and updates shadow metrics after each response.

## Configuring the GLM endpoint

`GLMIntegration` reads the endpoint and API key from environment variables by default.  Override them when instantiating the class or set `GLM_API_URL` and `GLM_API_KEY`:

```python
from INANNA_AI.glm_integration import GLMIntegration

glm = GLMIntegration(
    endpoint="https://api.example.com/glm41v_9b",
    api_key="<your key>",
)
```

When no arguments are provided the class falls back to the `GLM_API_URL` and
`GLM_API_KEY` environment variables and attaches the key as an
`Authorization: Bearer` header when present.

## Conversation loop

To engage the Albedo personality, create the layer and pass it to the orchestrator. The `INANNA_AI.main` script records microphone input and routes it through this layer:

```bash
export GLM_API_KEY=<your key>
export GLM_API_URL=https://api.example.com/glm41v_9b
python -m INANNA_AI.main --duration 3 --personality albedo
```

Each invocation cycles through Nigredo, Albedo, Rubedo and Citrinitas states before returning to Nigredo for a continuous loop. You can also use the layer programmatically:

```python
from orchestrator import MoGEOrchestrator
from INANNA_AI.personality_layers import AlbedoPersonality

layer = AlbedoPersonality()
orchestrator = MoGEOrchestrator(albedo_layer=layer)
```

Calling `orchestrator.route()` with `text_modality=True` will return the GLM reply reflecting the current state.

## Quantum personality context

Version 2 introduces an optional *quantum context* argument.  The
``AlchemicalPersona`` computes a sentence embedding for each message using
``MUSIC_FOUNDATION.qnl_utils.quantum_embed``.  ``AlbedoPersonality.generate_response``
accepts a ``quantum_context`` string which is forwarded to
``GLMIntegration.complete`` and inserted into the state templates in
``state_contexts``.  The persona updates its state weights using the embedding
and the current emotional weight from :mod:`INANNA_AI.emotion_analysis`.

```python
layer.generate_response("I love Alice", quantum_context="entangled")
```

## Examples

The persona inspects each message to detect emotional keywords and entity types.
State metrics are updated after the model replies.

```python
from INANNA_AI.personality_layers.albedo import AlchemicalPersona

core = AlchemicalPersona()
entity, triggers = core.detect_state_trigger("I love Alice")
print(entity)           # "person"
print(triggers)         # {"affection"}
core.update_metrics(triggers)
print(core.entanglement, core.shadow_balance)
```

When combined with ``AlbedoPersonality`` the detected entity and triggers are
inserted into the prompt:

```python
from INANNA_AI.personality_layers import AlbedoPersonality
layer = AlbedoPersonality()
reply = layer.generate_response("I love Alice")
```

The first call uses the ``nigredo`` template and yields a prompt like:

```
[Nigredo] (person) I love Alice affection
```

## Additional Personality Layers

The project also provides three lightweight layers that can be invoked through the orchestrator or the
`learning_mutator.py --activate` option. These layers colour the response tone without invoking the
remote GLM.

### Nigredo layer

Represents dissolution and shadow work. Replies are hushed and introspective:

```python
from INANNA_AI.personality_layers.nigredo_layer import NigredoPersonality
layer = NigredoPersonality()
print(layer.speak("welcome"))
```

Expected output resembles:

```
Nigredo whispers from the void: welcome
```

### Rubedo layer

Celebrates fiery transformation with a triumphant voice:

```python
from INANNA_AI.personality_layers.rubedo_layer import RubedoPersonality
layer = RubedoPersonality()
print(layer.speak("it is done"))
```

Which returns something like:

```
Rubedo proclaims with blazing heart: it is done
```

### Citrinitas layer

Guides the user toward clarity and enlightenment:

```python
from INANNA_AI.personality_layers.citrinitas_layer import CitrinitasPersonality
layer = CitrinitasPersonality()
print(layer.speak("proceed"))
```

Typical output is:

```
Citrinitas speaks in golden clarity: proceed
```

