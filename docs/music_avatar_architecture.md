# Music Avatar Architecture

The Crown agent can reflect on musical input by combining feature extraction
with language model reasoning.  The `music_llm_interface.py` helper analyses an
audio or MIDI file, packages the findings and forwards them to the Crown LLM
through `rag.orchestrator.MoGEOrchestrator`.

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
