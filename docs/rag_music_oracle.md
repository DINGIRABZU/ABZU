# RAG Music Oracle

`rag_music_oracle.py` answers questions about songs by combining Retrieval Augmented Generation with basic audio emotion analysis. It loads a local MP3 or WAV file, extracts coarse features via `INANNA_AI.emotion_analysis.analyze_audio_emotion()` and uses those values to enrich a query against the music corpus through `rag_engine.query()`.

If `--play` is specified the module also invokes `play_ritual_music.compose_ritual_music()` to generate a short melody representing the detected emotion. The resulting text answer and optional audio path are printed to the console.

## Usage

```bash
python rag_music_oracle.py "How does this MP3 express grief?" --audio song.mp3 --play
```

The script will report the dominant emotion, tempo and the highest scoring snippet retrieved from the corpus. When `--play` is enabled a small WAV file is written and played through `play_ritual_music.py`.

