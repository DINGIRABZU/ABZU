# Music Generation Usage

Generate audio from text prompts or ritual invocations.

## Command line

```bash
python music_generation.py "lofi beat"
```

## Ritual invocation

```python
from music_generation import register_music_invocation
from invocation_engine import invoke

register_music_invocation("\u266a")
invoke("\u266a [joy]")
```

## LLM bridge

```bash
python music_llm_interface.py --prompt "ambient pad"
```
