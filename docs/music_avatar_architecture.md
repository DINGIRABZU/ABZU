# Music Avatar Architecture

The Crown agent can reflect on musical input by combining feature extraction
with language model reasoning.  The `music_llm_interface.py` helper analyses an
audio or MIDI file, packages the findings and forwards them to the Crown LLM
through `rag.orchestrator.MoGEOrchestrator`, which can optionally persist
context using the `vector_memory` subsystem.

```bash
python music_llm_interface.py path/to/song.wav
```

The script performs the following steps:

1. **Feature extraction** – `pipeline.music_analysis` loads the file and derives
   MFCC, key, tempo and a coarse emotion label.
2. **Prompt construction** – the results are serialised to JSON and sent to the
   orchestrator as a prompt for **LLM CROWN**.
3. **Model response** – the orchestrator routes the prompt to the appropriate
   language model and returns a structured reply.

The JSON printed to `stdout` combines the analysis with the LLM response, making
it easy to feed musical context into higher level agents or pipelines.

For generating test tones during development, the
`seven_dimensional_music.generate_quantum_music` helper can synthesise a short
audio clip along with placeholder seven-plane analysis.

## Usage Examples

The `music_generation.py` script exposes a minimal interface for creating short
audio samples. Generation parameters such as **temperature**, **duration** and
random **seed** can be configured from the command line or when calling the
module programmatically. Streaming output is supported to allow incremental
playback or progressive file writing.

```bash
# generate a five second clip at low temperature
python music_generation.py "lofi beat" --duration 5 --temperature 0.7

# stream raw bytes while generating
python music_generation.py "riff" --stream | aplay -f cd
```

When used as a library:

```python
from music_generation import generate_from_text

gen = generate_from_text(
    "ambient pad",
    emotion="calm",
    tempo=90,
    temperature=0.8,
    duration=8,
    seed=42,
    stream=True,
)
for chunk in gen:
    ...  # handle each audio chunk
```

## Evaluation Workflow

Music prompts submitted through the web console are logged via
`corpus_memory_logging.log_interaction` together with any user supplied
feedback. A lightweight Streamlit dashboard under `dashboard/usage.py` summarises
interaction counts and feedback entries to help operators review generation
quality. These records can further feed the training guides and retraining
scripts to refine future models.
