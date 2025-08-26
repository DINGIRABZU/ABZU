# Testing Music Pipeline

To run the unit tests for the ritual music pipeline:

```bash
pytest tests/test_play_ritual_music.py::test_synthesize_melody_with_sf
pytest tests/test_play_ritual_music.py::test_synthesize_melody_without_sf
pytest tests/test_play_ritual_music.py::test_archetype_mix_soundfile_present
pytest tests/test_play_ritual_music.py::test_archetype_mix_fallback
pytest tests/test_audio_backends.py::test_get_backend_noop
pytest tests/test_play_ritual_music.py::test_ritual_profile_cached
```

These cover scenarios where the `soundfile` library is available and where the NumPy fallback and caching mechanisms are used.
